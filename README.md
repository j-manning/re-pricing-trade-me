# re-pricing-trade-me

Weekly scraper for **Trade Me Property** listing fees (New Zealand).

## Platform

Trade Me is New Zealand's dominant online marketplace, including property listings.

## Pricing Model

**Per-listing fee** based on the property's rateable value (RV):

| Tier | Rateable Value | Fee (NZD) |
|------|---------------|-----------|
| Standard | ≤ $450,000 | $99 |
| Premium | > $450,000 | $159 |

- `fee_period = per_listing`
- `currency = NZD`

Source: [Trade Me Property fees](https://help.trademe.co.nz/hc/en-us/articles/360032007872-Property-fees)

## Output

`data/pricing.csv` — 2 rows per scrape date, one per tier.

## Schema

See [shared schema](#shared-schema) — standard across all `re-pricing-*` repos.

```
scrape_date, platform, market, currency, tier_name, fee_amount, fee_period,
prop_value_min, prop_value_max, location_note, hybrid_note
```

## Running Locally

```bash
pip install -r requirements.txt
python scraper.py
```
