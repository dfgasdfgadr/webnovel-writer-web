/** Maps reader pulse weakness keywords to PolishAgent axes. */
export const WEAKNESS_TO_AXIS: Record<string, string[]> = {
  "节奏": ["pacing"],
  "拖沓": ["pacing"],
  "过快": ["pacing"],
  "太慢": ["pacing"],
  "AI味": ["ai_flavor"],
  "模板": ["ai_flavor"],
  "机械化": ["ai_flavor"],
  "对话": ["dialogue"],
  "对白": ["dialogue"],
  "描写": ["description"],
  "描述": ["description"],
  "情感": ["emotion"],
  "情绪": ["emotion"],
  "感动": ["emotion"],
  "钩子": ["hook"],
  "悬念": ["hook"],
  "吸引": ["hook"],
  "连贯": ["coherence"],
  "设定": ["consistency"],
  "OOC": ["consistency"],
  "人物": ["consistency"],
  "性格": ["consistency"],
  "逻辑": ["coherence"],
  "不通": ["coherence"],
  "转折": ["coherence"],
};

export function weaknessToAxes(weakness: string): string[] {
  const axes: string[] = [];
  for (const [keyword, mapped] of Object.entries(WEAKNESS_TO_AXIS)) {
    if (weakness.includes(keyword)) {
      axes.push(...mapped);
    }
  }
  return [...new Set(axes)];
}
