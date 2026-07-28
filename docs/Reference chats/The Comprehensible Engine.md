# The Comprehensible Engine
## A Full Context Document: Everything About the Idea, Where It Came From, What It Is, and Where It's Going
 
*Written June 2026. This document captures every detail of the idea, the full history of how it was developed, the research behind it, every technical decision, every pivot, and exactly where it stands today. Nothing is skipped.*
 
---
 
## Part 1: The Origin Story
 
### Where the idea came from
 
In April 2025, Jayon was a third-semester Digital Media Master's student at the University of Bremen. He was enrolled in a course called "AI Kind of Sucks: How to Actually Use Generative Media for Storytelling" run by instructor Fabian Mosele at HfK Bremen (fmosele@hfk-bremen.de). The course was a deliberate counter to the Silicon Valley AI hype narrative. Its philosophy: AI should be a facilitator of human creativity and storytelling, not a replacement. The course required students to create a project using generative media tools, which would be presented at a class exhibition at the end.
 
Most students were creating AI-generated short films or generative art pieces. Jayon went a different direction. Instead of creating a single video, he wanted to create a tool that used generative media as its engine. A tool that produced AI-generated video, but for a specific, useful, non-gimmicky purpose.
 
He was learning German at the time, sitting around B1 level, with Malayalam as his native language and English as his fluent second. He had been looking at YouTube channels for German comprehensible input content and kept noticing the same problem: the content was not entertaining enough. It was useful but dry. He could not sit and watch it for long. He wanted to keep learning but the format kept pulling him away.
 
That frustration became the seed of the idea.
 
### The first version of the idea
 
His first articulation was simple: what if you could generate a comprehensible input video on demand for any language, any level, in a style that was actually entertaining? A website where you pick your language, your level, give some keywords or a story idea, and the system builds you a short, level-appropriate video complete with narration, visuals, and subtitles.
 
He took this idea to Gemini (Google's AI) and spent several sessions doing deep research to turn it into a proper product plan. The output of those sessions became what he called the Comprehensible Engine Prototype Bible, a 31-page document covering pedagogy, product requirements, technical architecture, prompt engineering, UX design, and a sprint-by-sprint implementation roadmap.
 
That document is real, detailed, and still largely valid. It forms the foundation of everything that follows.
 
---
 
## Part 2: The Science Behind It (Why This Actually Works)
 
This section covers the pedagogical foundation that the whole tool is built on. Understanding this is not optional background reading. It is the core of why the product works and why it is different from every other language learning tool.
 
### Stephen Krashen and Second Language Acquisition
 
The theoretical backbone is the work of Dr. Stephen Krashen, a linguist whose theory of second language acquisition is one of the most influential and research-backed frameworks in the field. His theory has five hypotheses, but two of them are the bedrock of the Comprehensible Engine.
 
**The Acquisition-Learning Hypothesis.** Krashen argues that humans have two separate systems for developing competence in a language. Acquisition is subconscious, the way children pick up their mother tongue by being immersed in it. Learning is conscious, the grammar drills, vocabulary lists, and rule memorisation that most school-based language education relies on. Krashen's central claim is that acquisition is the mechanism that produces real fluency. Learning only produces explicit knowledge about the language, not the ability to actually use it. The Comprehensible Engine is designed entirely as an acquisition tool. It deliberately has no grammar drills, no quizzes, no explicit correction. Everything is designed to produce subconscious absorption.
 
**The Input Hypothesis (i+1).** This is the most actionable and specific part of Krashen's theory. It states that acquisition happens when a learner receives input that is just slightly beyond their current level of competence. Not so hard that it is incomprehensible and frustrating. Not so easy that nothing new is absorbed. Just one step ahead. The notation is i for the learner's current level and i+1 for the ideal input. The Comprehensible Engine's entire generation pipeline is designed to produce i+1 content programmatically: it maps the user's self-selected CEFR level to a known vocabulary set, then seeds the generated script with a small, controlled percentage of new vocabulary from the next level up, made understandable by the visual and narrative context around it.
 
**The Affective Filter Hypothesis.** This is the psychological part. Krashen observed that negative emotional states, specifically anxiety, boredom, embarrassment, and low self-confidence, raise a kind of mental filter that blocks language acquisition even when the learner is receiving perfectly calibrated i+1 input. A learner who is stressed or bored cannot acquire language efficiently. Conversely, a learner who is relaxed, engaged, and entertained has a low affective filter and absorbs language naturally. This is the insight that explains why entertaining, story-based video content is not a nice-to-have feature of the Comprehensible Engine. It is the core pedagogical mechanism. The stories, the visual engagement, the absence of tests and grades: all of it is engineering the learner's emotional state toward low anxiety and high engagement so that acquisition can happen.
 
**The vicious cycle this tool is designed to break.** Most language learners fall into a predictable failure loop. They encounter content that is too hard (beyond i+1), fail to understand it, feel frustrated and anxious (affective filter rises), the raised filter makes even good input less effective, they feel stuck and stagnant, and eventually quit. The Comprehensible Engine breaks this loop at the source by guaranteeing that every generated video is calibrated to the learner's level, ensuring comprehension, which produces a feeling of success, which keeps the affective filter low, which makes acquisition more efficient, which leads to greater comprehension. A virtuous cycle instead of a vicious one.
 
### CEFR and what it means practically
 
CEFR stands for Common European Framework of Reference for Languages. It is the international standard for describing language proficiency, running from A1 (complete beginner) through A2, B1, B2, C1, and C2 (mastery). Each level has published vocabulary lists and grammatical constraints.
 
For the Comprehensible Engine, CEFR is the spec that the AI generation pipeline has to enforce. A1 German means: present tense only, nominative case primarily, maximum sentence length of around eight to ten words, vocabulary from the Goethe-Institut A1 wordlist. A2 means introducing simple past, accusative case, and expanding vocabulary toward the A2 list. The system uses these constraints as hard rules in the script-generation prompts so that every output is genuinely appropriate for the selected level.
 
---
 
## Part 3: The Product Vision
 
### What the tool actually is
 
The Comprehensible Engine is a web-based tool that lets a user generate a short, AI-produced, comprehensible input video in any language at any CEFR level, on any topic they choose, in a style that is visually engaging and entertaining. The user inputs their preferences and the system handles everything else, producing a final video they can watch and absorb from, without needing to find, source, or create CI content themselves.
 
### The problem it solves
 
There are two problems it solves and they are related. First: high-quality comprehensible input is scarce. The best-known example is Dreaming Spanish, a YouTube channel in Spanish that has proved the format works at massive scale. But equivalents for other languages either do not exist or are lower quality, and none of them can be personalised to a specific learner's interests or level. Second: the CI content that does exist is not entertaining enough for many learners to sustain. If the affective filter is the key mechanism, and entertainment and engagement are the primary tools for keeping it low, then boring CI content is actually less effective CI content, not just less enjoyable. The tool solves both: it generates content on demand and it generates it in formats designed to be entertaining.
 
### The user experience vision
 
A learner comes to the website. They choose their target language (any language), their level (A1 through C2), and a story type or topic. They can either choose from preset options (a fairy tale, a travel story, a workplace scene, a comedy sketch) or type in a custom prompt describing exactly what they want. They can also just hit a randomise button if they have no specific idea.
 
The system then runs entirely in the background. A loading screen keeps them engaged with progress messages while five stages of AI generation happen automatically. A few minutes later, a video appears: a fully assembled, narrated, subtitled, level-appropriate short film in their target language, generated just for them, in an entertaining visual style.
 
They watch it. They understand it. They feel good. They come back for another one.
 
### Visual style: why whiteboard animation is the smart choice
 
The original prototype bible chose whiteboard animation as the default visual style, and this was one of the most important and least obvious decisions in the whole document. The reason is cognitive: research on multimedia learning shows that simpler, less visually complex formats produce better comprehension and recall than photorealistic video, because they reduce cognitive load. When a learner is simultaneously listening to narrated language, processing new vocabulary, and watching a scene, every extra visual detail (other people in a café, traffic outside a window, complex lighting) competes for cognitive resources that should be going to the language. A whiteboard drawing of two people at a table and two coffee cups eliminates all that noise and focuses attention on the linguistic input. Additionally, the gradual drawing process creates a sense of anticipation that holds attention. This is pedagogically superior to photorealistic video for a language learning context, not just aesthetically simpler. And as we will see in the technical section, it also sidesteps the single biggest technical problem in AI video generation: character consistency across multiple clips.
 
### Other video format options
 
The bible also identified several alternative formats that the user could choose from, each with its own pedagogical strengths:
 
Whiteboard narration style: the default, minimalist, low cognitive load, best for A1 and A2 beginners. Animated story: 2D cartoon style, colourful, character-driven, good for keeping engagement high. Gameplay narration: a story told through simple game-style visuals, good for younger learners or gamers. Human narration with images: a narrator (AI avatar) shown alongside related images, similar to how some YouTube CI channels work. Everyday slice-of-life: simple realistic scenes of daily situations, directly practical vocabulary.
 
---
 
## Part 4: The Five-Stage Pipeline (The Core of the System)
 
This is how the Comprehensible Engine actually works. Every user request flows through five sequential stages. The output of each stage becomes the input for the next. All data passes between stages in structured JSON format so that the pipeline is traceable, debuggable, and reliable.
 
### Stage 1: Story Concept Generation
 
The first stage takes the user's inputs (language, level, topic, story keywords or custom prompt) and passes them to an LLM with a carefully engineered prompt that enforces the CEFR pedagogical rules. The prompt uses few-shot prompting (showing the model examples of what a good A1 story structure looks like) to force a specific JSON output format containing: a story title, a list of characters with simple descriptions, a setting (a single noun phrase), and a plot summary broken into three to five sentences.
 
This stage does not write the full script yet. It produces a plan. The reason for this separation is reliability: asking the model to simultaneously plan a story, enforce vocabulary constraints, write full dialogue, and format for multiple stages in one prompt is a recipe for inconsistent output. Breaking it into steps forces the model to think logically and makes each output inspectable.
 
Output: StoryConcept.json
 
### Stage 2: Script Generation
 
The story concept JSON goes into a second LLM call with a Chain-of-Thought prompt that tells the model to think step by step through each plot point and expand it into a full scene. For each scene, the output contains two things: a line of dialogue or narration (in the target language, at the specified CEFR level, using constrained vocabulary), and a visual description of what should be seen on screen during that line (in English, written as a concrete, simple, animatable action that the video model can execute).
 
This separation between dialogue and visual description is critical. It means the audio generation and the video generation stages receive precisely the right input for each, rather than trying to infer one from the other.
 
Output: Script.json (an array of scene objects, each with dialogue and visual description)
 
### Stage 3: Audio Generation
 
Every line of dialogue from Script.json is wrapped in SSML (Speech Synthesis Markup Language) tags before being sent to a Text-to-Speech API. SSML allows control over the pace, pitch, and pausing of the synthesised speech. For a language learning context, the audio needs to be deliberately slower than natural speech, with clear articulation and strategic pauses between sentences to give the learner processing time. A half-second pause after each line is inserted via a break tag. The prosody tag sets the rate to slow.
 
This stage runs in parallel across all scenes, producing one audio file per scene.
 
The key decision here: the audio is generated separately from the video, not inside the video model. This gives much more control over the narration quality and pacing, which must meet specific pedagogical standards.
 
Output: One AudioFile.mp3 per scene
 
### Stage 4: Visual Generation
 
Each scene's visual description from Script.json is turned into a video prompt and sent to a text-to-video generation API. Every prompt is prefixed with a consistent style prefix that never changes between scenes. This style prefix is the consistency mechanism: because the prefix is identical for every clip, the visual style remains uniform throughout the video. An example prefix for whiteboard style: "whiteboard animation style, simple black and white line drawing, minimalist, focused on the action, clean background."
 
The full prompt structure is: style prefix + visual description from Script.json + camera angle specification.
 
Each clip is generated at around six to eight seconds long, which is the length of one narration line.
 
Output: One VideoClip.mp4 per scene
 
### Stage 5: Assembly
 
All the audio files and video clips are assembled into a final output video. The video clips are stitched in sequence. The audio tracks are overlaid in sync with their corresponding video clips. Subtitles are generated from the dialogue text and burned in or delivered as a separate track. The result is a complete, watchable, 30 to 60-second comprehensible input video.
 
This stage uses a programmatic video assembly tool (Creatomate, Shotstack, or FFmpeg-based code) rather than any AI generation. It is deterministic and fast.
 
Output: FinalOutput.mp4
 
---
 
## Part 5: The Original Research (What Gemini Found in April 2025)
 
The April 2025 Gemini research sessions produced what Jayon called the Prototype Bible. Here is a summary of the major findings and decisions from that research.
 
### Technology stack chosen at the time
 
Backend: FastAPI (Python) chosen over Django because FastAPI is async-native, crucial for managing multiple concurrent long-running AI API calls, and produces automatic API documentation. Django's full-stack features were unnecessary overhead for this API-centric orchestrator.
 
Frontend: SvelteKit chosen over Next.js/React because of smaller bundle sizes, better performance, a simpler developer experience, and faster load times from compiling to optimised vanilla JavaScript rather than running a virtual DOM.
 
Database and backend as a service: Supabase chosen over Firebase because it is built on standard PostgreSQL (relational model, better for structured learning application data), has more predictable pricing, and avoids vendor lock-in.
 
Local LLM: Ollama for running Llama 3 8B locally on the MacBook M3 Pro. Free, fast for development and testing, zero API cost per call during prototyping.
 
Task queue: Redis Queue (RQ) over Celery, because RQ is simpler to configure while still handling the asynchronous video generation task reliably.
 
Real-time communication: WebSockets over HTTP polling, so the server can push a "generation complete" message to the frontend instantly rather than the client repeatedly checking.
 
Video generation: Replicate as an API aggregator, giving access to open-source models like Hunyuan-DiT and Mochi through a single REST API without managing GPU infrastructure.
 
### Cost control strategy designed at the time
 
Use local Ollama for all LLM script-generation stages (zero cost). Use Google Cloud TTS free tier for audio. Use Replicate for video generation with strict limits on clip length (five to ten seconds per scene) and resolution. Cache identical requests so two users requesting the same video topic and level get the same cached result.
 
### The three-sprint implementation plan
 
Sprint 1 (weeks 1 and 2): Build the FastAPI backend, implement the multi-step LLM prompt chain using Ollama, set up Redis and RQ for async task management, create placeholder task for video generation, basic SvelteKit UI components.
 
Sprint 2 (weeks 3 and 4): Integrate cloud TTS and text-to-video APIs into the RQ worker task, implement FFmpeg video assembly, implement WebSocket endpoint for generation-complete notification, connect frontend to backend.
 
Sprint 3 (weeks 5 and 6): Build custom video player with interactive subtitles and playback speed controls, implement Supabase authentication, build user dashboard with video history, final polish.
 
### Why it was shelved in April 2025
 
One primary reason: the video generation models at the time were not good enough. The visual quality was poor, characters morphed and distorted between scenes, physics were wrong, and visual consistency across multiple clips generated separately was essentially impossible to guarantee. A story in which the protagonist looks different in every scene is not just an aesthetic failure: it is a cognitive disruption that raises exactly the affective filter the tool is trying to lower. The tool's entire value proposition was undermined by the technology not being ready yet.
 
Jayon cancelled the plan. He understood the idea was sound but the timing was wrong.
 
---
 
## Part 6: The 2026 Re-evaluation (What Has Changed)
 
In June 2026, Jayon revisited the idea against the current state of the technology. The reassessment was comprehensive and the conclusion was clear: the single thing he cancelled over has changed more than anything else in AI in the intervening period.
 
### What changed in video generation
 
The shift from 2025 to 2026 in video generation has been described by people in the field as equivalent to going from blurry phone cameras to professional cinema cameras in the space of a year. The specific improvements that matter for the Comprehensible Engine:
 
Veo 3.1 (Google DeepMind): Generates native 4K video with 48kHz synchronized audio in one pass. The model understands scene and character continuity. Capable of lip-synced dialogue. Available via API.
 
Kling 3.0 (Kuaishou): Introduced Multi-Shot Storyboard, a feature that lets you define multiple shots with individual prompts and generates all of them with maintained character consistency, lighting consistency, and scene continuity across the whole set. This is directly relevant to the Comprehensible Engine, where multiple clips of the same story need to look like they belong together.
 
Seedance 2.0: Approximately $0.30 per clip, making the cost of generating a five-scene 30-second video around $1.50 in video generation costs alone.
 
Image-to-video as a consistency tool: Professionals now use a technique where a reference image of the character or scene is generated once and then used as the visual anchor for all subsequent video clips of that character. This means the character looks the same in every scene because every clip is generated starting from the same reference image. This technique directly solves the consistency problem that caused the original cancellation.
 
The whiteboard style advantage is even more pronounced now: because whiteboard animation is stylistically simple and does not require realistic human faces or detailed environments, it sidesteps the consistency problem almost entirely. A line drawing looks consistent because line drawings inherently have fewer variables that can shift between clips.
 
### What changed in TTS and audio
 
TTS naturalness has improved significantly. ElevenLabs, Google TTS, and open-source alternatives are now capable of producing narration that sounds genuinely human-like with appropriate emotional inflection. The "not too AI" audio requirement that Jayon specified in his original Gemini conversations is now achievable without workarounds.
 
### What to avoid: Sora
 
The original research considered Sora (OpenAI). This is now definitively the wrong choice. Sora 2 is being discontinued: the web app was shut down on April 26, 2026, and the API will be shut down on September 24, 2026. Building anything on Sora right now means building on a deprecated platform. Route to Veo, Kling, or Seedance instead.
 
### What changed in the aggregator layer
 
In 2025 the recommendation was Replicate. In 2026 the faster, better-maintained option is fal.ai, which provides unified API access to Veo, Kling, Seedance, and others with competitive pricing and better reliability. Atlas Cloud and OpenCreator are also options for switching between video models behind a single API.
 
### What changed in the build tools
 
The three-sprint plan from April 2025 was written before vibe-coding environments (Cursor, Claude Code) made scaffolding full-stack AI applications significantly faster. The same architecture that would have taken six weeks to build manually in April 2025 can now be scaffolded in days with AI-assisted coding tools. This changes the calculation on whether to attempt the prototype before a course deadline or a job application.
 
---
 
## Part 7: The Competition Landscape
 
### Who else is doing this now
 
Text and audio comprehensible input generation is now largely solved as a category. Readlang, LingQ, and various graded reader generators can produce text-based CI material at any CEFR level in under a minute.
 
The closest direct competitors in the video space:
 
MeloLingua: offers story-based CI learning grounded explicitly in Krashen's i+1 framework, with personalised stories and native audio. Includes German. Free tier available. This is the most direct overlap.
 
Mootion: generates language-learning videos with character dialogue, CEFR levels, and contextual scenes. Primarily talking-character dialogue format.
 
Digen: AI-powered language learning videos.
 
HeyGen: an AI avatar video tool that has language learning applications.
 
Dreaming Spanish: not a generator but the proof of concept. A human-run YouTube channel in comprehensible Spanish that has demonstrated the format works at massive scale. The channel is the existence proof that people will watch this content and that it produces acquisition.
 
### The gap that still exists
 
Despite all of the above, the specific combination that makes the Comprehensible Engine distinctive does not yet exist as a finished product: genuinely entertaining, animated, multi-format, AI-generated CI video, with full pipeline automation, available for any language, any level, personalised to the learner's topic interests. MeloLingua is the closest but does not offer the video generation or visual entertainment component. Mootion is talking-head dialogue, not animated storytelling. The format that Dreaming Spanish proved works at scale (engaging, story-driven, visually interesting) has not been replicated by any automated AI tool yet.
 
---
 
## Part 8: The Updated Technical Stack (2026 Recommendations)
 
Given everything above, here is the updated recommendation for building the prototype in 2026.
 
LLM for script generation: Claude claude-sonnet-4-6 via Anthropic API, or Llama 3 locally via Ollama for zero-cost development runs. Claude is preferred for production because of its better instruction-following and structured JSON output reliability.
 
TTS for audio: ElevenLabs for the highest quality and most human-sounding output. Google Cloud TTS as a cheaper alternative. Both support SSML for pace and pause control.
 
Video generation: Kling 3.0 via fal.ai for the Multi-Shot Storyboard feature (built-in consistency). Veo 3.1 via Google Cloud for the native audio option (if you want to experiment with audio-inside-video rather than separate TTS). Seedance 2.0 for cost-effectiveness.
 
Video assembly: Creatomate or Shotstack via API rather than raw FFmpeg. These provide a visual template editor plus a batch-rendering API, which means the assembly step becomes a simple API call with JSON parameters rather than writing custom FFmpeg code.
 
Backend: FastAPI (unchanged from original, still the right choice).
 
Frontend: SvelteKit (unchanged, still appropriate) or a simpler option like a Streamlit or Gradio interface for an early prototype that does not need a polished UI.
 
Database: Supabase (unchanged).
 
Task queue: Redis Queue (unchanged) or n8n as the orchestration layer if you want a visual workflow you can modify without code changes.
 
Local development: Ollama on MacBook M3 Pro for all LLM calls during development. M3 Pro handles Llama 3 8B comfortably.
 
---
 
## Part 9: The MVP Scope (What to Actually Build First)
 
This is the most important section for deciding what to do next. Everything above is context. This is the action.
 
### The principle: strip it ruthlessly
 
The original Prototype Bible described a full product with authentication, a user dashboard, a video history library, interactive subtitle click-to-define, playback speed controls, and multiple language support. All of that is for version two. The first version has one job: prove that the pipeline works end to end and that the output is watchable and genuinely useful.
 
### The minimum viable prototype
 
One language: German (Jayon is learning it, he can evaluate the output quality, and it is the most relevant for his current context in Bremen).
 
One level: A1 (simplest constraints, easiest to verify correctness).
 
One format: whiteboard animation (sidesteps consistency problems, pedagogically superior for A1, technically simpler to prompt for).
 
One length: 30 seconds (four to five scenes at six to eight seconds each).
 
No authentication, no dashboard, no user accounts. Just a form: enter a topic or keywords, hit generate, watch the video.
 
### What the prototype proves
 
It proves the pipeline is real. It proves the JSON chaining works. It proves the CEFR constraints can be enforced in the script. It proves the audio sounds acceptable. It proves the visual clips can be generated consistently enough to tell a coherent story. It proves the assembly produces a watchable final video. That is enough to present at a course exhibition, enough to reference in a job application as a real project, and enough to know whether to build version two.
 
### The simplest possible end-to-end flow to build first
 
Before any framework or UI: just prove the core loop works in a Python script. Take a keyword (for example "two friends at a bakery"), generate a StoryConcept.json using a prompt to an LLM, generate a Script.json with dialogue and visual descriptions, generate one audio file for the first scene using ElevenLabs, generate one video clip for the first scene using Kling via fal.ai, assemble them with Creatomate. If that 8-second clip comes out correctly and the German A1 dialogue is at the right level, the concept is validated and the rest is engineering.
 
---
 
## Part 10: Why This Is Also a Perfect Learning Project
 
This project is being considered not only as a product but as a way to learn automation and pipeline building. It is worth being precise about why it is a particularly good teaching project.
 
The Comprehensible Engine forces you to engage with every hard part of a real automation pipeline simultaneously: structured LLM output (you cannot afford hallucinated JSON in this pipeline), chaining steps where one output feeds the next (the whole system breaks if StoryConcept.json is malformed), calling multiple external APIs (LLM, TTS, video generation, assembly), async task handling (video generation takes minutes, the user needs to wait without the server blocking), consistency requirements across multiple independent generations (the four scenes must feel like one story), and final delivery integration (the output is a real file the user watches, not a text response).
 
That combination is essentially the full anatomy of any production-grade automation pipeline. Learning it through this specific project means the knowledge transfers directly to any other pipeline in any other domain: product video generation, document processing, content automation, data pipelines. The skeleton is the same.
 
The durable skill being built is not "how to call the fal.ai API." That is a lookup. The durable skill is knowing where to put human checkpoints, how to handle failures gracefully, how to enforce a spec across a chain of probabilistic generators, and how to make a system reliable rather than just impressive in a demo. Those skills are not commoditising.
 
---
 
## Part 11: The Course Context and How to Frame It
 
The course "AI Kind of Sucks" has a specific philosophy that is directly relevant to how the Comprehensible Engine should be presented:
 
Avoid AI hype. Embrace AI limitations. Find the few well-crafted uses of generative tools where the limitations are owned and AI-native stories are told. Focus on facilitation, not full automation. Be critical of bias, datasets, and authorship.
 
The Comprehensible Engine fits this philosophy extremely well if framed correctly. The whiteboard style is a deliberate choice that owns what AI video generation cannot do well (photorealistic consistency) and leans into what it can do well (simple, consistent line drawings). The whole pipeline is transparent about where AI is doing the work and where the human (the learner's topic choice, the pedagogical framework, the CEFR constraints) is setting the spec. The tool is designed around a real, research-backed pedagogical theory, not around "AI is cool." And the output is honest: it does not pretend to be human-produced storytelling, it is AI-generated comprehensible input, which is exactly what it says it is.
 
A demo that is honest about its seams and explicit about the design decisions behind them will land far better in this course than one that claims to have solved everything. Fabian Mosele's whole course is a critique of the latter.
 
---
 
## Part 12: The Business Case (If This Becomes a Product)
 
### The market
 
Digital language learning is a large and growing market. The comprehensible input segment is proving itself at scale via Dreaming Spanish, which has built a large audience and demonstrates genuine acquisition outcomes. The gap is clear: Dreaming Spanish proves the demand, but it is a human-produced channel for one language. Automated, personalised, multi-language CI video is the logical extension and no one has built it well yet.
 
### Who would pay for it
 
Three user segments were identified in the original research:
 
Independent adult learners: people learning a language for travel, culture, work, or personal interest, who want an engaging, self-directed learning experience they can personalise. They pay subscription fees for Duolingo and Babbel; they would pay for something that demonstrably works better and is more entertaining.
 
Language teachers: educators who want to create CI material for their classes in any topic or at any level without having to source, edit, or produce videos themselves. A teacher plan with batch generation and classroom sharing features.
 
Content creators: people who run language-learning YouTube channels (like the channels Jayon was watching when he had the original idea) and want to generate additional content at scale, or to create personalised content for their Patreon subscribers.
 
### The revenue model from the original research
 
Phase 1 (launch): a generous free tier to build community and prove value, with a Pro subscription at around 10 to 15 euros per month for higher generation limits and more format options.
 
Phase 2 (scale): a Creator or Teacher plan with B2B features: ability to upload your own voice for narration, commercial rights to generated videos, batch generation, classroom tools, at around 30 to 50 euros per month.
 
### Cost economics
 
The original research estimated approximately $0.05 to $0.15 in API costs for a 30-second video at prototype quality. In 2026 with Seedance at $0.30 per clip and five clips per video, video generation alone is around $1.50. Plus LLM (approximately $0.01 with Claude), TTS (approximately $0.02 with ElevenLabs), and assembly (approximately $0.05 with Creatomate), a 30-second video costs approximately $1.58 to $1.70 in API costs. At a 10 euro per month Pro subscription with a limit of 20 videos per month, the gross margin per user is approximately 10 - (20 × 1.70) = negative. Cost optimisation (shorter clips, lower resolution, model switching) is critical for the business model to work. Alternatively, the free tier is limited to 3 videos per month and the Pro tier at 20 euros per month with 20 videos gives a slim positive margin.
 
---
 
## Part 13: Open Questions and Next Decisions
 
These are the things that still need to be decided before any building starts.
 
**Which video model to use first.** Kling 3.0's Multi-Shot Storyboard is the strongest argument for consistency in the early prototype. But Veo 3.1's native audio could simplify the pipeline by eliminating the separate TTS step. The choice depends on which matters more for the prototype: consistency across scenes (Kling) or pipeline simplicity (Veo). Recommendation: start with Kling for the consistency guarantee.
 
**Whiteboard specifically or animated 2D.** Whiteboard is the safest choice because it has the lowest cognitive load and sidesteps the most consistency problems. But if the goal includes showing entertaining visual storytelling, animated 2D might be more compelling for a course exhibition. The prototype should start with whiteboard and add styles as options later.
 
**Whether to use n8n or code for the orchestration.** n8n gives a visual workflow you can demonstrate and modify without code changes, which is useful for showing the pipeline in a presentation. Pure code (FastAPI plus Python scripts) is faster to iterate on and does not require a running n8n server. For a prototype being presented at a course exhibition, n8n makes the pipeline visible and explainable to an audience. For a production system, pure code is more reliable.
 
**When to start building.** The answer from every angle is now. The research is done. The decisions are clear. The only remaining learning comes from running the pipeline and seeing what breaks.
 
---
 
## Part 14: Full Source and Resource List
 
**Pedagogy and theory**
- Krashen's Input Hypothesis: https://en.wikipedia.org/wiki/Input_hypothesis
- Affective Filter explanation: https://www.colorincolorado.org/glossary/affective-filter
- CEFR levels overview: https://www.languagetesting.com/cefr-scale
- Goethe-Institut A1 German wordlist: https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf
- Dreaming Spanish (the proof of concept channel): https://www.youtube.com/@DreamingSpanish
**Existing tools and competitors**
- MeloLingua (closest current competitor): search MeloLingua language learning
- Mootion (AI language learning video): search Mootion AI
- LingQ (CI text platform): https://www.lingq.com
**Video generation**
- Kling 3.0 via fal.ai: https://fal.ai
- Veo via Google Cloud: https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos
- Seedance 2.0: search Seedance AI video
**Audio generation**
- ElevenLabs: https://elevenlabs.io
- SSML documentation (Microsoft): https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup
**Assembly and orchestration**
- Creatomate (template-based video assembly API): https://creatomate.com
- Creatomate plus n8n tutorial: https://creatomate.com/blog/how-to-automate-video-creation-with-n8n
- n8n templates (video automation): https://n8n.io/workflows/
- n8n automated video factory template: https://n8n.io/workflows/3442-fully-automated-ai-video-generation-and-multi-platform-publishing/
**Backend and infrastructure**
- FastAPI: https://fastapi.tiangolo.com
- SvelteKit: https://kit.svelte.dev
- Supabase: https://supabase.com
- Ollama (local LLM): https://ollama.ai
- fal.ai (AI model aggregator): https://fal.ai
---
 
## Summary: The Full Picture in One Place
 
The Comprehensible Engine began as a course project idea in April 2025. A Digital Media Master's student in Bremen, learning German, frustrated by how unentertaining the available comprehensible input YouTube content was, imagined a tool that could generate it on demand, personalised, in any language, at any level, in any visual style.
 
The idea was grounded in rigorous pedagogical science: Krashen's i+1 hypothesis and the affective filter. The whole system was designed as an emotional regulation environment for language acquisition, not just a content generator. The pipeline was thought through in detail across five sequential AI generation stages, from story concept to final assembled video, all held together by structured JSON passing between steps.
 
The tool was researched extensively and a full Prototype Bible was produced. Then it was shelved in April 2025 for one reason: the video models were not ready. The visual consistency problem meant the output was too poor to be useful.
 
In June 2026, the re-evaluation is clear. Video generation has changed more than any other AI capability in the intervening period. The specific problems that caused the cancellation, character consistency across clips and visual quality, are now largely solved by Kling 3.0's Multi-Shot Storyboard, image-to-video reference locking, and the collapse in cost per clip. The rest of the stack is still sound. The competition has grown but has not filled the specific niche of entertaining, animated, pedagogically grounded, multi-format CI video generation.
 
The narrow, buildable, immediately valuable MVP is: one 30-second German A1 whiteboard animation, end to end, with a Python script first, then a minimal web interface. Everything else comes after that clip exists.
 
The idea was right in April 2025. The timing was wrong. The timing is now right.