import React, { useState } from 'react';
import { SectionHeader } from './InfoPopover';
import type { GoalNode as StoreGoalNode } from '../store';

// Connector constants for layout tree rendering
const LINE_W = 14;        // width of the connector column
const LINE_PX = 1;        // line weight
const LINE_COLOR = 'rgba(0,0,0,0.13)';
const ARC_R = 7;          // border-radius of the arc turn

// DEV Deep Tree (5 levels) for ?devtree=1 testing
const DEV_DEFAULT_VIEW: StoreGoalNode[] = [
  { outcome_id: 'outcome 1', text: 'Style DNA & Production Bible', depth: 0, is_current: false },
  { outcome_id: 'outcome 4', text: 'Contrast Ratio Validation', depth: 3, is_current: false },
  { outcome_id: 'outcome 5', text: 'Final Verification Checklist', depth: 4, is_current: true },
];

const DEV_FULL_TREE: StoreGoalNode[] = [
  { outcome_id: 'outcome 1', text: 'Style DNA & Production Bible', depth: 0, parent: null, children: ['outcome 2', 'outcome 1-sibling'] },
  { outcome_id: 'outcome 1-sibling', text: 'Research & Inspirations', depth: 1, parent: 'outcome 1', children: [] },
  { outcome_id: 'outcome 2', text: 'Theme Configuration', depth: 1, parent: 'outcome 1', children: ['outcome 3', 'outcome 2-sibling'] },
  { outcome_id: 'outcome 2-sibling', text: 'Typography Scaling Rules', depth: 2, parent: 'outcome 2', children: [] },
  { outcome_id: 'outcome 3', text: 'Color Swatch Derivation', depth: 2, parent: 'outcome 2', children: ['outcome 4', 'outcome 3-sibling'] },
  { outcome_id: 'outcome 3-sibling', text: 'Accessibility Target Matrix', depth: 3, parent: 'outcome 3', children: [] },
  { outcome_id: 'outcome 4', text: 'Contrast Ratio Validation', depth: 3, parent: 'outcome 3', children: ['outcome 5', 'outcome 4-sibling'] },
  { outcome_id: 'outcome 4-sibling', text: 'Automated Contrast Unit Test', depth: 4, parent: 'outcome 4', children: [] },
  { outcome_id: 'outcome 5', text: 'Final Verification Checklist', depth: 4, is_current: true, parent: 'outcome 4', children: [] },
];

interface GoalSectionProps {
  goal: {
    default_view: StoreGoalNode[];
    full_tree: StoreGoalNode[];
  } | null;
}

// Single Goal Node Item
interface GoalNodeItemProps {
  label: string;
  isCurrent?: boolean;
  isRoot?: boolean;
  isDim?: boolean;
  showLine?: boolean;
  isLast?: boolean;
}

const GoalNodeItem: React.FC<GoalNodeItemProps> = ({
  label,
  isCurrent,
  isRoot,
  isDim,
  showLine,
  isLast,
}) => {
  const [hovered, setHovered] = useState(false);
  const dotSize = isCurrent ? 7 : isRoot ? 7 : 5;
  const dotColor = isCurrent ? 'var(--you)' : isRoot ? 'var(--text-primary)' : 'var(--text-muted)';
  const dotOpacity = isRoot ? 0.45 : isDim ? 0.4 : 1;

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'stretch',
        borderRadius: '2px',
        minHeight: '26px',
        backgroundColor: hovered ? 'rgba(0,0,0,0.03)' : 'transparent',
        marginLeft: isRoot ? '-6px' : '-4px',
        paddingLeft: isRoot ? '6px' : '4px',
        marginRight: '-4px',
        paddingRight: '4px',
        transition: 'background-color 0.1s',
      }}
    >
      {/* Connector column (YouTube comment style) */}
      {!isRoot && (
        <div
          style={{
            width: `${LINE_W}px`,
            marginRight: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          {/* vertical line segment above arc */}
          {showLine ? (
            <div style={{ width: `${LINE_PX}px`, flex: '0 0 8px', backgroundColor: LINE_COLOR }} />
          ) : (
            <div style={{ flex: '0 0 8px' }} />
          )}

          {/* L-shaped arc turn */}
          <div
            style={{
              width: `${LINE_W - 2}px`,
              height: '9px',
              borderLeft: `${LINE_PX}px solid ${LINE_COLOR}`,
              borderBottom: `${LINE_PX}px solid ${LINE_COLOR}`,
              borderBottomLeftRadius: `${ARC_R}px`,
              flexShrink: 0,
            }}
          />

          {/* vertical segment continuing below node */}
          {!isLast && (
            <div style={{ width: `${LINE_PX}px`, flex: 1, minHeight: '4px', backgroundColor: LINE_COLOR }} />
          )}
        </div>
      )}

      {/* Node Content */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          minWidth: 0,
          padding: '4px 0',
          flex: 1,
          opacity: isDim ? 0.45 : 1,
        }}
      >
        <div
          style={{
            width: `${dotSize}px`,
            height: `${dotSize}px`,
            borderRadius: '50%',
            backgroundColor: dotColor,
            opacity: dotOpacity,
            flexShrink: 0,
            boxShadow: isCurrent ? '0 0 0 2.5px rgba(0, 87, 255, 0.15)' : 'none',
          }}
        />
        <span
          style={{
            fontSize: isCurrent || isRoot ? '12px' : '11px',
            fontWeight: isCurrent || isRoot ? 600 : 400,
            color: isCurrent || isRoot ? 'var(--text-primary)' : 'var(--text-muted)',
            lineHeight: '1.3',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            textAlign: 'left',
          }}
          title={label}
        >
          {label}
        </span>
      </div>
    </div>
  );
};

// Expanded tree structure rendering
interface FullNode {
  id: string;
  label: string;
  isCurrent: boolean;
  children: FullNode[];
}

const buildTreeStructure = (
  nodes: StoreGoalNode[],
  parentId: string | null
): FullNode[] => {
  return nodes
    .filter((n) => n.parent === parentId)
    .map((n) => ({
      id: n.outcome_id,
      label: n.text,
      isCurrent: !!n.is_current,
      children: buildTreeStructure(nodes, n.outcome_id),
    }));
};

interface ExpandedTreeProps {
  nodes: FullNode[];
  depth?: number;
  currentId: string;
}

const ExpandedTree: React.FC<ExpandedTreeProps> = ({ nodes, depth = 0, currentId }) => {
  if (nodes.length === 0) return null;
  return (
    <div style={{ paddingLeft: depth > 0 ? `${LINE_W + 8}px` : 0 }}>
      {nodes.map((node, i) => {
        const isLast = i === nodes.length - 1;
        const isCurrent = node.id === currentId;
        return (
          <div key={node.id}>
            <GoalNodeItem
              label={node.label}
              isCurrent={isCurrent}
              showLine={true}
              isLast={isLast && node.children.length === 0}
            />
            {node.children.length > 0 && (
              <ExpandedTree
                nodes={node.children}
                depth={depth + 1}
                currentId={currentId}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

export const GoalSection: React.FC<GoalSectionProps> = ({ goal }) => {
  const [expanded, setExpanded] = useState(false);

  // Check URL query parameters for ?devtree=1
  const isDevTree = new URLSearchParams(window.location.search).get('devtree') === '1';

  // Choose tree data: fixture vs hardcoded devtree
  const defaultView = isDevTree ? DEV_DEFAULT_VIEW : goal?.default_view || [];
  const fullTreeData = isDevTree ? DEV_FULL_TREE : goal?.full_tree || [];

  if (defaultView.length === 0) {
    return (
      <div style={{ borderBottom: '1px solid var(--border)' }}>
        <SectionHeader label="Goal" sectionKey="GOAL" />
        <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
            Start a new chat
          </div>
        </div>
      </div>
    );
  }

  // Find the emphasized current goal node id
  const currentGoalNode = defaultView.find(n => n.is_current);
  const currentId = currentGoalNode?.outcome_id || '';

  // Parse root node
  const rootNode = defaultView[0];
  const lastNode = defaultView[defaultView.length - 1];

  // Check if we need to insert the expander chip in collapsed view
  // Hidden chip exists if the depth difference between root and the next node is > 1
  const hasHiddenNodes = defaultView.length > 1 && (defaultView[1].depth - defaultView[0].depth) > 1;
  const hiddenCount = hasHiddenNodes ? (defaultView[1].depth - defaultView[0].depth - 1) : 0;

  // Build recursive children nodes for expanded view
  const rootTreeId = fullTreeData.find(n => n.parent === null)?.outcome_id || null;
  const treeStructure = buildTreeStructure(fullTreeData, rootTreeId);

  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      <SectionHeader label="Goal" sectionKey="GOAL" />
      <div
        style={{
          padding: '0 16px 12px',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: expanded ? '260px' : 'none',
          overflowY: expanded ? 'auto' : 'visible',
        }}
      >
        {!expanded ? (
          /* Collapsed View (Thread-Collapse) */
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {/* Root Node */}
            <GoalNodeItem
              label={rootNode.text}
              isRoot={true}
              isLast={defaultView.length === 1}
            />

            {/* Hidden Chip */}
            {hasHiddenNodes && (
              <div
                style={{
                  minHeight: '24px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    width: `${LINE_W}px`,
                    marginRight: '8px',
                    height: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <div style={{ width: `${LINE_PX}px`, height: '100%', backgroundColor: LINE_COLOR }} />
                </div>
                <button
                  onClick={() => setExpanded(true)}
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    backgroundColor: 'var(--panel)',
                    border: '1.5px solid var(--border)',
                    borderRadius: '4px',
                    padding: '2px 8px',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 500,
                  }}
                >
                  ⌄ {hiddenCount} more
                </button>
              </div>
            )}

            {/* Intermediate ancestors (if depth = 2, i.e., d=2 has no chip but has 3 lines total) */}
            {defaultView.map((node, idx) => {
              if (idx === 0 || node.is_current) return null;
              // Skip if it's the element immediately after root when chip is rendered (it is already represented after the chip)
              if (hasHiddenNodes && idx === 1 && defaultView.length > 2) return null;
              
              return (
                <GoalNodeItem
                  key={node.outcome_id}
                  label={node.text}
                  isDim={true}
                  showLine={true}
                  isLast={false}
                />
              );
            })}

            {/* Current Node (Emphasized leaf) */}
            {lastNode !== rootNode && (
              <GoalNodeItem
                label={lastNode.text}
                isCurrent={true}
                showLine={true}
                isLast={true}
              />
            )}

            {/* Show Full Tree text toggle at the bottom (if d <= 2 and tree is not empty) */}
            {!hasHiddenNodes && fullTreeData.some(n => n.parent !== null) && (
              <button
                onClick={() => setExpanded(true)}
                style={{
                  fontSize: '10px',
                  color: 'var(--text-muted)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  paddingLeft: `${LINE_W + 8 + 9 + 8}px`, // Align with current node text
                  fontFamily: 'var(--font-mono)',
                  marginTop: '4px',
                  textAlign: 'left',
                  alignSelf: 'flex-start',
                }}
              >
                ⌄ show full tree
              </button>
            )}
          </div>
        ) : (
          /* Expanded View (Full Hierarchy tree) */
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {/* Root node */}
            <GoalNodeItem
              label={rootNode.text}
              isRoot={true}
              isLast={treeStructure.length === 0}
            />

            {/* Full recursive tree branches */}
            <ExpandedTree
              nodes={treeStructure}
              currentId={currentId}
            />

            {/* Show Less toggle */}
            <button
              onClick={() => setExpanded(false)}
              style={{
                fontSize: '10px',
                color: 'var(--text-muted)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                paddingLeft: '4px',
                fontFamily: 'var(--font-mono)',
                marginTop: '8px',
                textAlign: 'left',
                alignSelf: 'flex-start',
              }}
            >
              ↑ show less
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
