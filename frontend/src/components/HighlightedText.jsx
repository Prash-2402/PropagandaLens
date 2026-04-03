import { useState } from 'react';
import { Info } from 'lucide-react';

export default function HighlightedText({ spans, originalText }) {
  const [hoveredSpan, setHoveredSpan] = useState(null);

  if (!spans || spans.length === 0) {
    return (
      <div className="text-gray-300 whitespace-pre-wrap leading-relaxed">
        {originalText}
      </div>
    );
  }

  // Sort spans by start index
  const sortedSpans = [...spans].sort((a, b) => a.start - b.start);
  
  const segments = [];
  let lastIndex = 0;

  sortedSpans.forEach((span, idx) => {
    // Add text before span
    if (span.start > lastIndex) {
      segments.push({
        type: 'text',
        content: originalText.substring(lastIndex, span.start),
        id: `text-${idx}`
      });
    }

    // Add span
    segments.push({
      type: 'span',
      content: originalText.substring(span.start, span.end),
      spanData: span,
      id: `span-${idx}`
    });

    lastIndex = span.end;
  });

  // Add remaining text
  if (lastIndex < originalText.length) {
    segments.push({
      type: 'text',
      content: originalText.substring(lastIndex),
      id: `text-last`
    });
  }

  return (
    <div className="relative">
      <div className="text-gray-200 whitespace-pre-wrap leading-loose text-lg font-serif">
        {segments.map((seg) => {
          if (seg.type === 'text') {
            return <span key={seg.id}>{seg.content}</span>;
          }

          const { technique, confidence, explanation, color } = seg.spanData;
          return (
            <span 
              key={seg.id}
              onMouseEnter={() => setHoveredSpan(seg.spanData)}
              onMouseLeave={() => setHoveredSpan(null)}
              className="relative rounded px-1 py-0.5 mx-0.5 cursor-pointer transition flex-inline"
              style={{ backgroundColor: `${color}30`, borderBottom: `2px solid ${color}` }}
            >
              {seg.content}
            </span>
          );
        })}
      </div>

      {/* Floating Tooltip */}
      {hoveredSpan && (
        <div 
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl p-4 z-10 transition-opacity animate-in fade-in"
          style={{ borderTop: `4px solid ${hoveredSpan.color}` }}
        >
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-bold text-gray-100">{hoveredSpan.technique}</h4>
            <span className="text-xs font-semibold bg-gray-800 px-2 py-1 rounded text-gray-300">
              {hoveredSpan.confidence}% Conf.
            </span>
          </div>
          <p className="text-xs text-gray-400">
            {hoveredSpan.explanation}
          </p>
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 border-8 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
}
