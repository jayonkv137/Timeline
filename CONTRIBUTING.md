# Contributing to Agency Panel (The Comprehensible Engine)

Thank you for your interest in contributing! We want to make it as easy and transparent as possible to contribute to this project. 

## 1. Development Workflow
The repository relies on a very structured workflow using spec documents. **Please read the `docs/` folder** before making significant architectural changes. The primary specs are:
- `PANEL_SPEC.md`
- `INTERACTION_SPEC.md`
- `COTRACE_PIPELINE_SPEC`

## 2. Pull Request Process
1. **Fork the repo** and create your branch from `master`.
2. If you've added code that should be tested, **add tests**.
3. If you've changed APIs, **update the documentation**.
4. Ensure the test suite passes on both the backend engine and the React frontend.
5. Submit a pull request with a detailed explanation of your changes.

## 3. Running Tests
### Frontend (`web/`)
We use Vitest and React Testing Library for frontend testing.
```bash
cd web
npm run test
```

### Backend (`engine/`)
We use `pytest` for backend testing.
```bash
cd engine
pytest
```

## 4. Code Style Rules
- Frontend code should use strict TypeScript types and the project's existing color variables (e.g. `--you:#0057FF; --ai:#E85A0A;`).
- Backend Python code should strictly follow PEP 8 and use Pydantic/JSON schemas for robust validation.
- All structural logic must align with the definitions established in `data/chats/`.

## 5. Reporting Issues
If you encounter a bug or have a spec question, please create an issue or log it in `SPEC_QUESTIONS.md` if you are an internal collaborator. Include a minimal reproducible example when reporting bugs.
