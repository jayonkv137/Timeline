#!/usr/bin/env python3
"""scripts/rename_corpus.py - Rename corpus folders and update manifest/meta to c<NN>_<task_type>_<length>."""
import glob
import json
import os
import shutil

RENAME_MAP = {
    "c01": ("creative", "long"),
    "c02": ("coding", "long"),
    "c03": ("coding", "short"),
    "c04": ("writing", "short"),
    "c05": ("research", "medium"),
    "c06": ("planning", "long"),
    "c07": ("research", "short"),
    "c08": ("writing", "short"),
    "c09": ("creative", "short"),
    "c10": ("research", "short"),
    "c11": ("research", "medium"),
    "c12": ("creative", "medium"),
    "c13": ("creative", "long"),
    "c14": ("coding", "medium"),
    "c15": ("creative", "medium"),
    "c16": ("research", "short"),
    "c17": ("research", "short"),
    "c18": ("research", "long"),
    "c19": ("creative", "long"),
    "c20": ("coding", "short"),
    "c21": ("debugging", "medium"),
    "c22": ("writing", "long"),
    "c23": ("creative", "medium"),
    "c24": ("planning", "short"),
    "c25": ("creative", "long"),
    "c26": ("planning", "medium"),
    "c27": ("creative", "short"),
    "c28": ("creative", "medium"),
    "c29": ("research", "medium"),
    "c30": ("creative", "short"),
    "c31": ("creative", "long"),
    "c32": ("creative", "long"),
    "c33": ("creative", "medium"),
    "c34": ("planning", "long"),
    "c35": ("coding", "long"),
    "c36": ("coding", "long"),
}

def main():
    corpus_root = "data/corpus"
    dirs = sorted([d for d in glob.glob(f"{corpus_root}/c*") if os.path.isdir(d)])
    id_map = {}

    for d in dirs:
        old_id = os.path.basename(d)
        prefix = old_id[:3]
        if prefix in RENAME_MAP:
            tt, lb = RENAME_MAP[prefix]
            new_id = f"{prefix}_{tt}_{lb}"
            id_map[old_id] = new_id
            new_dir = os.path.join(corpus_root, new_id)
            
            # Update meta.yaml
            meta_path = os.path.join(d, "meta.yaml")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    txt = f.read()
                txt = txt.replace(f"id: {old_id}", f"id: {new_id}")
                with open(meta_path, "w", encoding="utf-8") as f:
                    f.write(txt)
            
            # Update source_meta.json
            sm_path = os.path.join(d, "source_meta.json")
            if os.path.exists(sm_path):
                with open(sm_path, "r", encoding="utf-8") as f:
                    sm = json.load(f)
                sm["chat_id"] = new_id
                with open(sm_path, "w", encoding="utf-8") as f:
                    json.dump(sm, f, indent=2, ensure_ascii=False)
                    f.write("\n")
            
            # Rename folder if changed
            if d != new_dir:
                os.rename(d, new_dir)
                print(f"Renamed: {old_id} -> {new_id}")

    # Update manifest.json
    manifest_path = os.path.join(corpus_root, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for c in manifest.get("chats", []):
            if c["id"] in id_map:
                c["id"] = id_map[c["id"]]
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("Updated manifest.json with renamed IDs.")

    # Create golden_01 from c15_creative_medium
    c15_dir = os.path.join(corpus_root, "c15_creative_medium")
    golden_dir = os.path.join(corpus_root, "golden_01")
    if os.path.exists(c15_dir) and not os.path.exists(golden_dir):
        shutil.copytree(c15_dir, golden_dir)
        # Create expected.md template
        expected_md = """# golden_01 — Hand-Labeled Benchmark Worksheet
**Source:** c15_creative_medium (Portfolio about page redesign)  
**Pairs:** 8  
**Task Type:** creative  
**Format:** claude_web_json  

## Overview
This conversation develops a creative portfolio About page concept pivoting from a text scroll narrative to an Attenborough-style AI film about the creative technologist.

## Pair Inventory & Attribution Expectations
- Pair 1: User requests review of current about page; AI reconstructs GSAP scroll-scrub narrative.
- Pair 2: User proposes AI hybrid film concept; AI shapes creative tensions and scope.
- Pair 3: User establishes Attenborough nature doc narrator spine; AI locks structure and flags voice-cloning constraint.
- Pairs 4-8: Script development, shot progression, visual style specifications.
"""
        with open(os.path.join(golden_dir, "expected.md"), "w", encoding="utf-8") as f:
            f.write(expected_md)
        print("Created data/corpus/golden_01/ from c15_creative_medium with expected.md.")

if __name__ == "__main__":
    main()
