#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMAS = {
    "navigation": {
        "required": {"label": str, "href": str},
        "optional": {"label_fr": str, "href_fr": str, "class": str, "target": str, "rel": str},
    },
    "skills": {
        "required": {"domain": str, "tags": list},
        "optional": {"domain_fr": str},
    },
    "timeline": {
        "required": {"year": str, "role": str, "description": str},
        "optional": {"year_fr": str, "role_fr": str, "description_fr": str},
    },
    "resources": {
        "required": {
            "icon": str,
            "title": str,
            "description": str,
            "href": str,
            "more": str,
        },
        "optional": {"title_fr": str, "description_fr": str, "more_fr": str},
    },
}

APPROVED_SITE_DATA = {
    "navigation": [
        {
            "label": "About",
            "label_fr": "À propos",
            "href": "/about/",
            "href_fr": "/fr/a-propos/"
        },
        {
            "label": "Portfolio",
            "label_fr": "Réalisations",
            "href": "/portfolio/",
            "href_fr": "/fr/realisations/"
        },
        {
            "label": "Blog",
            "label_fr": "Blogue",
            "href": "/blog/",
            "href_fr": "/fr/blogue/"
        },
        {
            "label": "Resume",
            "label_fr": "CV",
            "href": "/resume/",
            "href_fr": "/fr/cv/"
        },
        {
            "label": "Now",
            "label_fr": "Maintenant",
            "href": "/now/"
        },
        {
            "label": "My LabML",
            "label_fr": "Mon LabML",
            "href": "https://app.dominicdapice.com/",
            "class": "nav-labml",
            "target": "_blank",
            "rel": "noopener"
        },
        {
            "label": "Sky of the day",
            "label_fr": "Ciel du jour",
            "href": "/sky/",
            "href_fr": "/fr/ciel/",
            "class": "nav-sky"
        }
    ],
    "skills": [
        {
            "domain": "Cloud & Data",
            "domain_fr": "Infonuagique et données",
            "tags": [
                "Azure",
                "Databricks",
                "VMware",
                "Azure DevOps"
            ]
        },
        {
            "domain": "IaC & Automation",
            "domain_fr": "IaC et automatisation",
            "tags": [
                "Ansible",
                "Terraform",
                "Packer",
                "GitHub Actions",
                "PowerShell",
                "Bash"
            ]
        },
        {
            "domain": "Languages",
            "domain_fr": "Langages",
            "tags": [
                "Python",
                "R",
                "JavaScript",
                "Perl"
            ]
        },
        {
            "domain": "Systems",
            "domain_fr": "Systèmes",
            "tags": [
                "Red Hat",
                "SUSE",
                "Windows",
                "IBM AIX",
                "Red Hat Satellite"
            ]
        },
        {
            "domain": "Databases",
            "domain_fr": "Bases de données",
            "tags": [
                "PostgreSQL",
                "MSSQL",
                "MySQL",
                "Oracle"
            ]
        },
        {
            "domain": "ML & Data",
            "domain_fr": "ML et données",
            "tags": [
                "MLOps",
                "DataOps",
                "Machine Learning",
                "Kaggle"
            ]
        }
    ],
    "timeline": [
        {
            "year": "2026 - NOW",
            "year_fr": "2026 - AUJOURD'HUI",
            "role": "Developer - Azure Infrastructure AI",
            "description": "Azure for AI · Databricks platform · MLOps / DataOps · IaC · CI/CD",
            "role_fr": "Développeur - infrastructure Azure pour l'IA",
            "description_fr": "Azure pour l'IA · plateforme Databricks · MLOps / DataOps · IaC · CI/CD"
        },
        {
            "year": "2018 - 2025",
            "role": "Cloud / Linux Administrator & IaC Developer",
            "description": "Self-service cloud for business clients · IaC in NERC-regulated environments",
            "role_fr": "Administrateur infonuagique et Linux, développeur IaC",
            "description_fr": "Infonuagique libre-service pour les clients d'affaires · IaC en environnements réglementés NERC"
        },
        {
            "year": "2015 - 2018",
            "role": "IT Standardization Linux System Administrator",
            "description": "Fleet of 1000+ servers · patching and standardization at scale",
            "role_fr": "Administrateur de systèmes Linux, standardisation des TI",
            "description_fr": "Parc de plus de 1 000 serveurs · mises à jour et standardisation à grande échelle"
        },
        {
            "year": "2011 - 2015",
            "role": "IT Linux System Administrator",
            "description": "Physical & virtual server deployments · Linux appliances",
            "role_fr": "Administrateur de systèmes Linux",
            "description_fr": "Déploiement de serveurs physiques et virtuels · appareils Linux"
        },
        {
            "year": "2001 - 2011",
            "role": "IT Linux System Administrator",
            "description": "Installation and configuration of servers and Linux appliances",
            "role_fr": "Administrateur de systèmes Linux",
            "description_fr": "Installation et configuration de serveurs et d'appareils Linux"
        },
        {
            "year": "1998 - 2001",
            "role": "IT Technician & System Administrator",
            "description": "Internal IT and client support - where it all started",
            "role_fr": "Technicien informatique et administrateur de systèmes",
            "description_fr": "Soutien informatique interne et aux clients : là où tout a commencé"
        }
    ],
    "resources": [
        {
            "icon": "🌌",
            "title": "Astronomy",
            "description": "Exploring celestial objects and following the latest discoveries - from JWST deep fields to backyard skies.",
            "href": "/blog/astronomy/",
            "more": "Read articles →",
            "title_fr": "Astronomie",
            "description_fr": "Explorer les objets célestes et suivre les dernières découvertes, des champs profonds de JWST au ciel de la cour arrière.",
            "more_fr": "Lire les articles (EN) →"
        },
        {
            "icon": "🧠",
            "title": "Artificial Intelligence",
            "description": "Studying ML advances and how they translate into real-world impact - then testing myself on Kaggle.",
            "href": "/blog/ai/",
            "more": "Read articles →",
            "title_fr": "Intelligence artificielle",
            "description_fr": "Étudier les avancées du ML et leur effet dans le monde réel, puis me mettre à l'épreuve sur Kaggle.",
            "more_fr": "Lire les articles (EN) →"
        },
        {
            "icon": "⚛️",
            "title": "Physics",
            "description": "Fascinated by the fundamental laws that describe our universe - the original distributed system.",
            "href": "/blog/physics/",
            "more": "Read articles →",
            "title_fr": "Physique",
            "description_fr": "Fasciné par les lois fondamentales qui décrivent notre univers, le premier système distribué.",
            "more_fr": "Lire les articles (EN) →"
        }
    ]
}


class SiteDataError(ValueError):
    pass


def _validate_string(value: Any, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SiteDataError(f"{location} must be a non-empty string")


def _validate_item(name: str, index: int, item: Any) -> None:
    location = f"{name}[{index}]"
    if not isinstance(item, dict):
        raise SiteDataError(f"{location} must be a mapping")

    schema = SCHEMAS[name]
    allowed = set(schema["required"]) | set(schema["optional"])
    unexpected = set(item) - allowed
    if unexpected:
        raise SiteDataError(
            f"{location} contains unexpected fields: {', '.join(sorted(unexpected))}"
        )

    for field, expected_type in schema["required"].items():
        if field not in item:
            raise SiteDataError(f"{location} is missing required field '{field}'")
        value = item[field]
        if not isinstance(value, expected_type):
            raise SiteDataError(
                f"{location}.{field} must be {expected_type.__name__}"
            )
        if expected_type is str:
            _validate_string(value, f"{location}.{field}")

    for field, expected_type in schema["optional"].items():
        if field in item:
            if not isinstance(item[field], expected_type):
                raise SiteDataError(
                    f"{location}.{field} must be {expected_type.__name__}"
                )
            _validate_string(item[field], f"{location}.{field}")

    if name == "skills":
        tags = item["tags"]
        if not tags:
            raise SiteDataError(f"{location}.tags must not be empty")
        for tag_index, tag in enumerate(tags):
            _validate_string(tag, f"{location}.tags[{tag_index}]")

    if name == "navigation":
        target_present = "target" in item
        rel_present = "rel" in item
        if target_present != rel_present:
            raise SiteDataError(f"{location} must define target and rel together")
        if target_present and (
            item["target"] != "_blank"
            or item["rel"] != "noopener"
            or not item["href"].startswith("https://")
        ):
            raise SiteDataError(
                f"{location} external links require https, target '_blank', and rel 'noopener'"
            )


def load_site_data(root: Path | str) -> dict[str, list[dict[str, Any]]]:
    data_dir = Path(root) / "_data"
    loaded: dict[str, list[dict[str, Any]]] = {}

    for name in SCHEMAS:
        path = data_dir / f"{name}.yml"
        if not path.is_file():
            raise SiteDataError(f"required data file is missing: {path}")
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise SiteDataError(f"{path} contains invalid YAML: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise SiteDataError(f"{path} must contain a non-empty list")
        for index, item in enumerate(data):
            _validate_item(name, index, item)
        if data != APPROVED_SITE_DATA[name]:
            raise SiteDataError(
                f"{name} does not match the approved content and order"
            )
        loaded[name] = data

    return loaded


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        data = load_site_data(root)
    except SiteDataError as exc:
        print(f"Site data validation failed: {exc}", file=sys.stderr)
        return 1

    counts = ", ".join(f"{name}={len(items)}" for name, items in data.items())
    print(f"Site data validation passed: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
