import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config.settings import LLMConfig
from config.sources import SOURCES
from extractors.llm_extractor import correct_edital, extract_edital
from extractors.llm_judge import evaluate
from extractors.pdf_extractor import extract_text_from_url
from scrapers.capes_scraper import CAPESScraper
from scrapers.fapdf_scraper import FAPDFScraper
from scrapers.funcap_scraper import FUNCAPScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


async def run_pipeline(config: LLMConfig | None = None, output_dir: Path | None = None) -> None:
    config = config or LLMConfig()
    out = output_dir or OUTPUT_DIR
    out.mkdir(exist_ok=True)

    # Construído aqui para que patches de teste substituam as classes corretamente
    scraper_registry = {
        "FAPDFScraper": FAPDFScraper,
        "FUNCAPScraper": FUNCAPScraper,
        "CAPESScraper": CAPESScraper,
    }

    all_editais = []
    all_evaluations = []

    for source_name, source_config in SOURCES.items():
        scraper_class = scraper_registry.get(source_config["scraper"])
        if scraper_class is None:
            logger.error(f"[{source_name}] Scraper '{source_config['scraper']}' não registrado.")
            continue

        scraper = scraper_class(source_config)
        logger.info(f"[{source_name}] Buscando oportunidades...")

        try:
            opportunities = await scraper.get_opportunities()
        except Exception as e:
            logger.error(f"[{source_name}] Falha ao buscar oportunidades: {e}")
            continue

        logger.info(f"[{source_name}] {len(opportunities)} oportunidades encontradas.")
        errors = 0

        for opportunity in opportunities:
            try:
                pdf_urls = await scraper.get_documents(opportunity)
                if not pdf_urls:
                    logger.warning(f"[{source_name}] Nenhum PDF em '{opportunity['titulo']}'")
                    continue

                pdf_url = pdf_urls[0]
                logger.info(f"[{source_name}] Extraindo PDF: {pdf_url}")

                pdf_text, text_truncated = await extract_text_from_url(pdf_url)

                edital, messages = await extract_edital(
                    pdf_text=pdf_text,
                    link_edital=opportunity["url"],
                    fonte=source_name,
                    config=config,
                )

                evaluation = await evaluate(
                    edital=edital,
                    source_text=pdf_text,
                    config=config,
                    json_valid=True,
                    text_truncated=text_truncated,
                )

                if evaluation.overall_score < config.correction_threshold:
                    logger.warning(
                        f"[{source_name}] Score baixo ({evaluation.overall_score:.2f}) em "
                        f"'{opportunity['titulo']}' — tentando correção multi-turn."
                    )
                    score_before = evaluation.overall_score

                    edital = await correct_edital(
                        messages=messages,
                        field_scores=evaluation.field_scores,
                        config=config,
                    )

                    evaluation = await evaluate(
                        edital=edital,
                        source_text=pdf_text,
                        config=config,
                        json_valid=True,
                        text_truncated=text_truncated,
                    )
                    evaluation.corrected = True
                    evaluation.score_before_correction = score_before
                    evaluation.score_after_correction = evaluation.overall_score

                    logger.info(
                        f"[{source_name}] Score após correção: {evaluation.overall_score:.2f}"
                    )

                all_editais.append(edital.model_dump(mode="json"))
                all_evaluations.append(evaluation.model_dump(mode="json"))
                logger.info(f"[{source_name}] '{opportunity['titulo']}' concluído.")

            except Exception as e:
                logger.error(f"[{source_name}] Falha em '{opportunity['titulo']}': {e}")
                errors += 1
                continue

        logger.info(f"[{source_name}] Concluído. Erros: {errors}/{len(opportunities)}.")

    editais_path = out / "editais.json"
    evaluation_path = out / "evaluation.json"

    with open(editais_path, "w", encoding="utf-8") as f:
        json.dump(all_editais, f, ensure_ascii=False, indent=2)
    logger.info(f"Salvo: {editais_path} ({len(all_editais)} editais)")

    with open(evaluation_path, "w", encoding="utf-8") as f:
        json.dump(all_evaluations, f, ensure_ascii=False, indent=2)
    logger.info(f"Salvo: {evaluation_path} ({len(all_evaluations)} avaliações)")


if __name__ == "__main__":
    config = LLMConfig()
    asyncio.run(run_pipeline(config))
