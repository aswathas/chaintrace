import { BehaviorTag } from '@/lib/types';

interface BehaviorTagsProps {
  tags: BehaviorTag[];
}

export function BehaviorTags({ tags }: BehaviorTagsProps) {
  if (tags.length === 0) {
    return (
      <div className="text-ink-300 text-sm">No behavior patterns detected</div>
    );
  }

  return (
    <div className="space-y-3">
      {tags.map((tag, idx) => (
        <div
          key={idx}
          className="bg-white/5 border border-white/10 rounded-apple-md p-3"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-ink-50 text-sm">{tag.tag}</span>
            <span className="text-xs bg-white/10 px-2 py-1 rounded-apple text-ink-200">
              {Math.round(tag.score * 100)}%
            </span>
          </div>
          <p className="text-xs text-ink-300">{tag.description}</p>
        </div>
      ))}
    </div>
  );
}
