import os

filepath = r'C:\Users\gokul\.gemini\antigravity\brain\f13ff3a2-9454-4fd2-a9a1-0612c5f6f992\frontend\src\EarlyWarningCenter.jsx'
filepath = os.path.abspath('frontend/src/EarlyWarningCenter.jsx')

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Update getSeverityColors
old_colors = \"\"\"  const getSeverityColors = (severity) => {
    switch(severity) {
      case 'CRITICAL': return 'bg-red-50 text-red-700 border-red-300';
      case 'WARNING': return 'bg-orange-50 text-orange-700 border-orange-300';
      case 'ADVISORY': return 'bg-amber-50 text-amber-700 border-amber-300';
      case 'WATCH': return 'bg-yellow-50 text-yellow-700 border-yellow-300';
      default: return 'bg-blue-50 text-blue-700 border-blue-300';
    }
  };\"\"\"

new_colors = \"\"\"  const getSeverityColors = (severity) => {
    switch(severity) {
      case 'CRITICAL': return 'bg-red-600 text-white border-red-700 shadow-sm';
      case 'WARNING': return 'bg-orange-500 text-white border-orange-600 shadow-sm';
      case 'ADVISORY': return 'bg-amber-400 text-amber-900 border-amber-500 shadow-sm';
      case 'WATCH': return 'bg-yellow-400 text-yellow-900 border-yellow-500 shadow-sm';
      default: return 'bg-blue-500 text-white border-blue-600 shadow-sm';
    }
  };\"\"\"

content = content.replace(old_colors, new_colors)

# Replace the activeAlertList.map block using a very generic regex
old_map = re.search(r'\{activeAlertList\.map\(alert => \(\s*<div key=\{alert\.alert_id.*?</div>\s*</div>\s*\)\)\}?', content, flags=re.DOTALL).group(0)

new_map = \"\"\"{activeAlertList.map(alert => (
  <div key={alert.alert_id} className={g-white rounded-xl shadow-sm border transition-all duration-200 hover:shadow-md cursor-pointer } onClick={() => setSelectedAlert(alert)}>
    <div className=\"p-5 flex flex-col md:flex-row gap-5 items-start\">
      {/* SEVERITY BADGE */}
      <div className=\"flex-shrink-0 flex flex-col items-center justify-center w-28 md:border-r border-slate-100 md:pr-5\">
        <div className={px-3 py-1.5 rounded-md text-[11px] font-black tracking-wider uppercase w-full text-center border }>
          {alert.severity}
        </div>
        <div className=\"text-[10px] font-mono text-slate-400 mt-3 text-center bg-slate-50 px-2 py-1 rounded w-full\">
          ID: {alert.alert_id.substring(0,8)}
        </div>
      </div>
      
      {/* MAIN CONTENT */}
      <div className=\"flex-grow w-full\">
        <div className=\"flex justify-between items-start mb-2\">
          <h3 className=\"text-sm md:text-base font-bold text-slate-800 uppercase tracking-wide\">
            {alert.hazard.replace('_', ' ')} COMPOUND THREAT
          </h3>
          <span className=\"text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100\">{new Date(alert.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
        </div>
        
        <p className=\"text-sm text-slate-600 font-medium mb-4\">{alert.trigger}</p>
        
        <div className=\"flex flex-wrap gap-3\">
          <div className=\"bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg min-w-[110px]\">
            <p className=\"text-[9px] uppercase text-slate-500 font-bold mb-1\">LEAD TIME</p>
            <p className=\"text-xs font-mono font-bold text-slate-800\">{alert.lead_time}</p>
          </div>
          <div className=\"bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg min-w-[110px]\">
            <p className=\"text-[9px] uppercase text-slate-500 font-bold mb-1\">CONFIDENCE</p>
            <p className=\"text-xs font-mono font-bold text-slate-800\">{alert.confidence}</p>
          </div>
          <div className=\"bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg flex-grow\">
            <p className=\"text-[9px] uppercase text-slate-500 font-bold mb-1\">PRIORITY ASSET</p>
            <p className=\"text-xs font-mono font-bold text-slate-800 truncate\">
              {alert.affected_assets?.length > 0 ? alert.affected_assets[0].name || alert.affected_assets[0].code : 'None'}
            </p>
          </div>
        </div>
      </div>
      
      {/* ACTION */}
      <div className=\"hidden md:flex items-center justify-center self-stretch pl-2\">
        <ChevronRight className=\"w-5 h-5 text-slate-400 group-hover:text-indigo-500 transition-colors\" />
      </div>
    </div>
  </div>
))}\"\"\"

content = content.replace(old_map, new_map)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)