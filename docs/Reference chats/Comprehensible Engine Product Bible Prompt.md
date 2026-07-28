### **Master Prompt for Generating "The Comprehensible Engine" Product Bible**

**Instructions for the Language Model:**

You are a multi-disciplinary team of experts tasked with creating a comprehensive "Product Bible" for a new startup called "The Comprehensible Engine." Your team includes:

* A **Chief Product Officer** with experience in EdTech.  
* A **PhD in Second Language Acquisition** specializing in Stephen Krashen's theories.  
* A **Lead Systems Architect** focused on scalable, cost-effective cloud solutions.  
* A **Senior UX/UI Designer** with a portfolio of intuitive consumer applications.

Your goal is to generate a complete, detailed, and actionable set of documents based on the provided structure. For each section, adopt the persona of the relevant expert, think critically, provide creative solutions, and justify your decisions. The output must be professional, detailed, and ready to guide the development of a real-world product.

### **BEGIN PROMPT**

#### **Phase 1: Strategic & Foundational Documents (The "Why")**

**Document 1: Project Vision & Mission Statement**

*(Persona: Chief Product Officer)*

* **Vision Statement:** Refine and expand upon the initial vision: "To empower language learners and educators by transforming any story idea into a scientifically-grounded, entertaining, and comprehensible learning experience." Make it more evocative and memorable.  
* **Mission Statement:** Create a clear, concise mission statement (2-3 sentences) that defines what we do, who we serve, and what makes us unique.  
* **Core Values:** Define 3-5 core company values that will guide our product decisions (e.g., "Pedagogy-First," "Learner-Centric Design," "Creative Empowerment").

**Document 2: Market Research & Competitive Analysis**

*(Persona: Chief Product Officer)*

* **Market Landscape:** Provide a summary of the current digital language learning market, highlighting the rise of video-based learning and Comprehensible Input (CI) methods.  
* **Competitive Matrix:** Create a Markdown table comparing "The Comprehensible Engine" against at least three key competitors:  
  1. **A Gamified App:** (e.g., Duolingo)  
  2. **A Content-Based Platform:** (e.g., FluentU or LingQ)  
  3. **A Typical CI YouTube Channel:** (e.g., "German with Anja" or similar)  
* **Matrix Columns:** Compare them on: Target Audience, Core Methodology, Content Personalization, Engagement Factor, Pricing Model, and Key Weakness.  
* **Unique Selling Proposition (USP):** Based on the analysis, write a paragraph clearly defining our USP. Why are we 10x better than the alternatives? (Hint: Focus on on-demand creation, personalization, and entertainment value).

**Document 3: Business Model Canvas**

*(Persona: Chief Product Officer)*

* Flesh out a complete Business Model Canvas. Be specific and creative with your suggestions.  
* **Customer Segments:** Detail at least 3 distinct segments (e.g., Independent Adult Learners, K-12 Language Teachers, Professional Content Creators).  
* **Value Propositions:** Tailor a specific value proposition for each segment.  
* **Revenue Streams:** Propose a phased revenue model.  
  * **Phase 1 (Launch):** A generous free tier to build community, with a "Pro" subscription for higher limits and more features.  
  * **Phase 2 (Scale):** A "Creator/Teacher" plan with B2B features (e.g., uploading your own likeness/voice, commercial rights to videos). Detail the pricing for each tier.  
* **Cost Structure:** Estimate the primary monthly costs, focusing on API usage. Create a sample calculation: "If 1 video costs X cents in API calls, and we have Y users generating Z videos, our estimated monthly cost is..."

**Document 4: Product Requirements Document (PRD) for V1.0 (The Prototype)**

*(Persona: Chief Product Officer)*

* **Introduction & Goal:** State the primary goal of the V1.0 prototype.  
* **User Personas:** Create two detailed user personas:  
  1. **"Alex,"** a 25-year-old hobbyist learner struggling with motivation.  
  2. **"Maria,"** a high school language teacher looking for better classroom materials.  
* **User Stories:** Write at least 5 user stories from the perspective of Alex and Maria, following the format: "As a \[persona\], I want to \[action\], so that I can \[benefit\]."  
* **Feature Scope:** Detail the features listed in the "Prototype Scope" (Guided Mode, 2 formats, etc.). For each feature, describe its functionality in detail.  
* **Success Metrics:** How will we measure the prototype's success? Define 3 key metrics (e.g., "Weekly Active Users," "Video Completion Rate," "User-Reported 'Helpfulness' Score").

#### **Phase 2: Pedagogical & Content Documents (The "How It Teaches")**

**Document 5: The Comprehensible Input (CI) Pedagogical Framework**

*(Persona: PhD in Second Language Acquisition)*

* **Abstract:** Write a brief abstract summarizing our pedagogical approach, citing Stephen Krashen.  
* **Level-Specific Breakdown (A1 & A2):** Create a detailed table for levels A1 and A2.  
  * **Columns:** Level, Description of Learner, Permitted Grammar, Max Sentence Length, Vocabulary Strategy, Example "+1" Concepts.  
  * **Content:** Fill this with specific, research-backed details. For A1 German, for example, grammar would be limited to present tense, simple W-questions, and nominative case.  
* **Format-Specific Pedagogy:** Explain how the CI principles are applied differently for "Animated Story" vs. "Narrator Slideshow." (e.g., "The slideshow format relies on zero ambiguity between the image and the narrated word, making it ideal for absolute A1 learners.")

**Document 6 & 7: Master Prompting Engine & Generation Specification**

*(Persona: PhD, collaborating with Systems Architect)*

* **The Master Orchestrator Prompt:** Write the complete, detailed system prompt for the main LLM that will control the entire pipeline. This prompt should instruct the LLM to act as a "language education expert" and follow all subsequent rules.  
* **Dynamic Prompt Templates:** Provide the exact prompt templates that will be filled with user input.  
  * **Script Generation Template:** Show how user inputs like {language}, {level}, and {story\_idea} are inserted into a larger prompt that contains the pedagogical rules.  
  * **Visual Prompt Augmentation Template:** Detail the logic for turning a script line into a visual prompt. Provide 3 examples for different formats (e.g., how "The bird flies" becomes a prompt for an animated story vs. a whiteboard drawing).  
  * **SSML Audio Generation Template:** Provide a template showing how the generated script is wrapped in SSML tags \<speak\>...\</speak\> with dynamic \<emphasis\> and \<break\> tags added by the LLM to create natural-sounding speech. Justify the standard pause length (\<break time="..."/\>) based on cognitive processing time for learners.

#### **Phase 3 & 4: Technical & Design Documents (The "How It's Built & Looks")**

**Document 8 & 9: System Architecture & Technical Stack**

*(Persona: Lead Systems Architect)*

* **Architecture Diagram:** Describe the components of a detailed flowchart (as text). Explain the flow of data from user request to final video, mentioning every service (Vercel, Render, Supabase, AI APIs).  
* **Technology Justification:** For each chosen technology (FastAPI, SvelteKit, Supabase), write a short paragraph justifying *why* it's the best choice for this prototype, focusing on performance, cost, and developer experience.  
* **API Cost Mitigation Strategy:** Detail a plan to control costs. Include:  
  1. **Model Selection:** Specify the exact models to use (e.g., "Groq Llama-3-8b for scripting, ElevenLabs free tier for TTS, Playground AI v2.5 for image generation"). Justify these choices based on cost-per-call and quality.  
  2. **Rate Limiting:** Plan for API-level rate limits to prevent abuse.  
  3. **Caching:** Propose a simple caching strategy (e.g., "If two users request the exact same video, serve the cached result from storage instead of regenerating").

**Document 12 & 13: UX/UI Design & Mockups**

*(Persona: Senior UX/UI Designer)*

* **Design Philosophy:** Write a paragraph on the design philosophy. "Clean, encouraging, and joyful. The UI should feel like a creative tool, not a complex machine. We will use soft colors, rounded corners, and subtle animations to create a welcoming environment that reduces learning anxiety."  
* **Wireframe Descriptions:** Describe, in text, the layout of the main "Guided Mode" page. Specify the layout, spacing, and interaction of each of the 6 UI/UX breakdown steps. Describe the loading state (e.g., "After clicking generate, a progress bar appears with encouraging, randomized messages like 'Brewing your story...' or 'Teaching the AI German...'").

### **END PROMPT**