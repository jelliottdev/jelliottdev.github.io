"""Validate completed drafts with the publication rules without changing the site."""
import argparse
import json
import re

from build_experiments import ROOT, article_link_aliases, require, validate_family, validate_record, validate_record_placement
from experiment_taxonomy import apply_classifications


def preflight(identifiers, root=ROOT):
    pages = {page['id'] for page in json.loads((root / 'data/index.json').read_bytes())['pages']}
    published = json.loads((root / 'data/experiments.json').read_bytes())['records']
    by_id = {record['id']: record for record in published}
    selected = []
    require(len(identifiers) == len(set(identifiers)), 'Duplicate requested record ID')
    for identifier in identifiers:
        require(re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier), 'Invalid record ID')
        path = root / 'experiments/records' / identifier / 'record.json'
        record = validate_record(root, path, pages)
        selected.append(record)
        by_id[identifier] = record
    taxonomy = root / 'data/method-families.json'
    if taxonomy.exists():
        apply_classifications(json.loads(taxonomy.read_text(encoding='utf-8')), list(by_id.values()))
    validate_record_placement(root, selected)
    for record in selected:
        require(all(identifier in by_id and identifier != record['id']
                    for identifier in record['related']), 'Related IDs must be published or in this batch')
        validate_family(record, by_id)
        article_link_aliases(root, record, set(by_id))
    return selected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ids', nargs='+', help='Completed record IDs; draft status is retained')
    args = parser.parse_args()
    records = preflight(args.ids)
    for record in records:
        print(f"PASS: {record['id']} - schema, declared bytes, plan, article, related IDs and family differences")
    print('No scripts executed, no outcomes certified, no site files changed. Build derived views only after review; this command publishes nothing.')
