import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class CatalogLoader:
    def __init__(self):
        self.catalog_path = settings.CATALOG_PATH
        self.scraped_url = "https://www.shl.com/solutions/products/"
        logger.info(f"Initialized CatalogLoader pointing to {self.catalog_path}")

    def load_catalog(self) -> List[Dict[str, Any]]:
        """Loads catalog from local JSON, or attempts to scrape and merge if possible."""
        local_data = []
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                    logger.info(f"Loaded {len(local_data)} assessments from local catalog.")
            except Exception as e:
                logger.error(f"Error reading local catalog file: {e}")
        else:
            logger.warning(f"Local catalog file not found at: {self.catalog_path}")

        # Attempt to scrape and merge to satisfy web scraping requirements
        try:
            scraped_data = self.scrape_catalog()
            if scraped_data:
                local_data = self._merge_catalogs(local_data, scraped_data)
                self._save_catalog(local_data)
        except Exception as e:
            logger.warning(f"Live scraping failed or skipped: {e}. Falling back purely to local catalog.")

        if not local_data:
            # Fallback if everything is empty (should not happen since we pre-load data/shl_catalog.json)
            raise RuntimeError("SHL assessment catalog is empty and could not be loaded or scraped.")

        return local_data

    def scrape_catalog(self) -> List[Dict[str, Any]]:
        """Scrapes the public SHL solutions page. Reverts gracefully if blocked."""
        logger.info(f"Attempting to scrape SHL assessments from: {self.scraped_url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )
        }
        
        try:
            response = requests.get(self.scraped_url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"SHL site returned status code {response.status_code}. Scraping aborted.")
                return []
                
            soup = BeautifulSoup(response.text, "html.parser")
            scraped_items = []
            
            # Look for typical product/solution grids, links, and cards
            # Note: SHL's actual site contains product cards matching 'card' or 'product-link'
            cards = soup.find_all(["div", "a"], class_=["card", "product-card", "solutions-card"])
            
            for idx, card in enumerate(cards):
                name_elem = card.find(["h3", "h4", "span"], class_=["title", "card-title"])
                name = name_elem.text.strip() if name_elem else ""
                
                desc_elem = card.find(["p", "div"], class_=["description", "card-text"])
                desc = desc_elem.text.strip() if desc_elem else ""
                
                link = card.get("href") if card.name == "a" else None
                if not link:
                    link_elem = card.find("a")
                    link = link_elem.get("href") if link_elem else ""
                
                if link and not link.startswith("http"):
                    link = "https://www.shl.com" + link
                
                if name:
                    scraped_items.append({
                        "name": name,
                        "description": desc or f"Scraped individual test solution: {name}.",
                        "url": link or self.scraped_url,
                        "skills": [name.split()[-1] if name.split() else "General"],
                        "duration": 30, # Default duration fallback
                        "languages": ["English"],
                        "adaptive_support": False,
                        "remote_support": True,
                        "category": "Cognitive Ability" if "Verify" in name else "Behavioral & Situational",
                        "job_roles": ["General Professional"],
                        "test_type": "Cognitive" if "Verify" in name else "Behavioral"
                    })
                    
            logger.info(f"Successfully scraped {len(scraped_items)} items from SHL website.")
            return scraped_items
            
        except Exception as e:
            logger.warning(f"Error scraping SHL catalog: {e}")
            return []

    def _merge_catalogs(self, local: List[Dict[str, Any]], scraped: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merges local database and scraped items, resolving duplicates by assessment name."""
        merged_dict = {item["name"].lower(): item for item in local}
        
        for item in scraped:
            name_key = item["name"].lower()
            if name_key not in merged_dict:
                merged_dict[name_key] = item
                logger.info(f"Merged new scraped assessment: {item['name']}")
            else:
                # Update existing items with fresh URLs or descriptions if they differ
                if item["url"] and item["url"] != self.scraped_url:
                    merged_dict[name_key]["url"] = item["url"]
                    
        return list(merged_dict.values())

    def _save_catalog(self, data: List[Dict[str, Any]]) -> None:
        """Saves catalog list back to local JSON file."""
        try:
            os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Saved catalog back to shl_catalog.json")
        except Exception as e:
            logger.error(f"Failed to write catalog file: {e}")
