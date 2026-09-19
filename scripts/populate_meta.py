#!/usr/bin/env python3
"""scripts/populate_meta.py - Populate meta.yaml fields across data/corpus/."""
import glob
import os
import re

METADATA = {
    "c01": {
        "task_type": "creative", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 10, "max_req": 80,
        "notes": "Collaborative photographic styling and art direction for a period 1930s Kerala Catholic wedding photo."
    },
    "c02": {
        "task_type": "coding", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 10, "max_req": 60,
        "notes": "Iterative frontend architecture and 3D Three.js integration for personal portfolio website."
    },
    "c03": {
        "task_type": "coding", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 2, "max_req": 10,
        "notes": "Brief continuation resolving 3D portfolio setup environment issues."
    },
    "c04": {
        "task_type": "writing", "language": "en", "prompt_style": "vague",
        "mode_hint": "centaur", "direction_hint": "user_heavy",
        "min_req": 2, "max_req": 15,
        "notes": "Ideation session exploring accessible analogies for AI automation styles (cyborg, centaur, autopilot)."
    },
    "c05": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 5, "max_req": 20,
        "notes": "Academic literature search and synthesis on computational creativity, co-creativity, and design systems."
    },
    "c06": {
        "task_type": "planning", "language": "en", "prompt_style": "vague",
        "mode_hint": "autopilot", "direction_hint": "ai_heavy",
        "min_req": 20, "max_req": 120,
        "notes": "Long presentation planning session clarifying scope and structure for an upcoming scientific talk on AI creativity."
    },
    "c07": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "centaur", "direction_hint": "user_heavy",
        "min_req": 2, "max_req": 15,
        "notes": "Methodological inquiry distinguishing AI-stated plans from genuine user requirements in human-AI interaction."
    },
    "c08": {
        "task_type": "writing", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 2, "max_req": 10,
        "notes": "Copywriting and content shaping for an Adidas product video case study on personal portfolio."
    },
    "c09": {
        "task_type": "creative", "language": "en", "prompt_style": "vague",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 2, "max_req": 12,
        "notes": "Visual analysis evaluating lighting contrast and background separation across reference photos."
    },
    "c10": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "centaur", "direction_hint": "user_heavy",
        "min_req": 1, "max_req": 5,
        "notes": "Direct user reflection asking AI to quantify and explain attribution of contributions across project artifacts."
    },
    "c11": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 5, "max_req": 25,
        "notes": "Deep dive into language acquisition workflows, spaced repetition mechanics, and Anki card architectures."
    },
    "c12": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 8, "max_req": 30,
        "notes": "Prompt engineering and style transfer experiments translating character portraits into Midjourney scene environments."
    },
    "c13": {
        "task_type": "creative", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 20, "max_req": 100,
        "notes": "Extensive character design dialogue evolving visual identity, lore, and styling for a Berliner raver sausage character."
    },
    "c14": {
        "task_type": "coding", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 10, "max_req": 40,
        "notes": "Manual Step 1a through Stage 4 execution session that produced fixture_pair1. Archived as provenance: pipeline_run."
    },
    "c15": {
        "task_type": "creative", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 5, "max_req": 25,
        "notes": "Portfolio About page redesign pivoting from text narrative to an Attenborough-style AI film about the creative technologist."
    },
    "c16": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "centaur", "direction_hint": "user_heavy",
        "min_req": 1, "max_req": 5,
        "notes": "Connecting academic paper 'Designing for Co-Creative Systems: 5 Paradoxes' to Timeline UI concepts."
    },
    "c17": {
        "task_type": "research", "language": "en", "prompt_style": "vague",
        "mode_hint": "copilot", "direction_hint": "ai_heavy",
        "min_req": 1, "max_req": 5,
        "notes": "Brief brainstorming query requesting research topic candidates for Datafied Society seminar."
    },
    "c18": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 15, "max_req": 70,
        "notes": "Comprehensive industry analysis dissecting aviation AI job description and corporate deployment strategies."
    },
    "c19": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 12, "max_req": 60,
        "notes": "Post-production video workflow coordinating Adobe clip exports for AI video model conditioning."
    },
    "c20": {
        "task_type": "coding", "language": "en", "prompt_style": "vague",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 2, "max_req": 10,
        "notes": "Auditing portfolio page assets and initiating conversion into reusable Figma components."
    },
    "c21": {
        "task_type": "debugging", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 5, "max_req": 25,
        "notes": "Technical debugging identifying causes of stuttering animations and optimizing GSAP / CSS masking transitions."
    },
    "c22": {
        "task_type": "writing", "language": "en", "prompt_style": "vague",
        "mode_hint": "autopilot", "direction_hint": "ai_heavy",
        "min_req": 10, "max_req": 70,
        "notes": "Long administrative assistance session drafting formal correspondence regarding tenancy verification in Bremen."
    },
    "c23": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 5, "max_req": 25,
        "notes": "Commercial product video direction defining fluid camera dolly movements and honey jar macro cinematography."
    },
    "c24": {
        "task_type": "planning", "language": "en", "prompt_style": "vague",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 3, "max_req": 15,
        "notes": "Production pre-planning defining shot list and visual constraints for a 5-shot hybrid action short film."
    },
    "c25": {
        "task_type": "creative", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 10, "max_req": 45,
        "notes": "Artistic look-development developing a hybrid aesthetic combining real production footage with AI stylized renders."
    },
    "c26": {
        "task_type": "planning", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 5, "max_req": 30,
        "notes": "Legal/administrative planning verifying immigration and student visa renewal procedures in Bremen."
    },
    "c27": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 1, "max_req": 8,
        "notes": "Animation prompt crafting for Kling 3.0 specifying upward motion and bioluminescent jellyfish dynamics."
    },
    "c28": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 5, "max_req": 30,
        "notes": "5-shot panning cinematography progression depicting intergenerational family growth in Kerala."
    },
    "c29": {
        "task_type": "research", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 5, "max_req": 25,
        "notes": "Explaining visual storytelling mechanics behind the Lando Norris effect and its application to brain page."
    },
    "c30": {
        "task_type": "creative", "language": "en", "prompt_style": "vague",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 2, "max_req": 10,
        "notes": "Worldbuilding ideation developing an educational story universe driven by autonomous AI characters."
    },
    "c31": {
        "task_type": "creative", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 15, "max_req": 80,
        "notes": "Family history documentary planning structuring archival photographs and AI video for centennial biography."
    },
    "c32": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 10, "max_req": 50,
        "notes": "Commercial creative direction specifying high-energy cinematography, lighting, and pacing for a Nike ad."
    },
    "c33": {
        "task_type": "creative", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 8, "max_req": 35,
        "notes": "Generative video prompt engineering tailoring Nike motion prompts for Seedance generation."
    },
    "c34": {
        "task_type": "planning", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 15, "max_req": 80,
        "notes": "Engineering workflow alignment establishing Phase 2 development rules and repository handoff."
    },
    "c35": {
        "task_type": "coding", "language": "en", "prompt_style": "mixed",
        "mode_hint": "copilot", "direction_hint": "balanced",
        "min_req": 15, "max_req": 90,
        "notes": "Frontend redesign implementing branch-based experience cards and timeline navigation on Technology page."
    },
    "c36": {
        "task_type": "coding", "language": "en", "prompt_style": "specified",
        "mode_hint": "copilot", "direction_hint": "user_heavy",
        "min_req": 12, "max_req": 60,
        "notes": "Technical specification review and schema design for Timeline data contracts and backend pipeline."
    }
}


def main():
    dirs = sorted([d for d in glob.glob("data/corpus/c*") if os.path.isdir(d)])
    print(f"Found {len(dirs)} corpus directories.")
    
    for d in dirs:
        cid_key = os.path.basename(d)[:3] # e.g. "c01"
        info = METADATA.get(cid_key)
        if not info:
            print(f"Warning: no metadata defined for {d}")
            continue
        
        meta_path = os.path.join(d, "meta.yaml")
        if not os.path.exists(meta_path):
            continue
        
        with open(meta_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        skip_owner = False
        
        for line in lines:
            if line.startswith("# TO BE COMPLETED BY THE OWNER"):
                skip_owner = True
                new_lines.append("# OWNER METADATA (COMPLETED)\n")
                new_lines.append(f"language: {info['language']}\n")
                new_lines.append(f"task_type: {info['task_type']}\n")
                new_lines.append(f"prompt_style: {info['prompt_style']}\n")
                new_lines.append("expected:\n")
                new_lines.append(f"  mode_hint: {info['mode_hint']}\n")
                new_lines.append(f"  direction_hint: {info['direction_hint']}\n")
                new_lines.append(f"  min_requirements: {info['min_req']}\n")
                new_lines.append(f"  max_requirements: {info['max_req']}\n")
                new_lines.append("notes: >\n")
                new_lines.append(f"  {info['notes']}\n")
                break
            new_lines.append(line)
        
        with open(meta_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
    print("All meta.yaml files populated successfully.")

if __name__ == "__main__":
    main()
