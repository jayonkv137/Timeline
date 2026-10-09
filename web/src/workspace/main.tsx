import { createRoot } from 'react-dom/client';
import { Workspace } from './Workspace';
import '../design-system/tokens/tokens.css';
import './workspace.css';
createRoot(document.getElementById('root')!).render(<Workspace/>);
