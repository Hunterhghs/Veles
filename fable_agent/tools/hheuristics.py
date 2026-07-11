"""H Heuristics domain-specific tools for Veles.

Registered automatically: validate_dashboard, fetch_data_source, market_sizing.
"""
from pathlib import Path
from fable_agent.tools.base import Tool, ToolResult

class ValidateDashboardTool(Tool):
    name = "validate_dashboard"
    description = "Validate a dashboard HTML for common issues: Chart.js CDN, viewport meta, semantic structure, KPI cards, canvas elements, data embedding, design tokens."
    parameters = {"type":"object","properties":{"path":{"type":"string","description":"Path to dashboard HTML."}},"required":["path"]}
    def execute(self, path: str) -> ToolResult:
        fp = Path(path)
        if not fp.exists(): return ToolResult(output=f"ERROR: {path} not found.", success=False)
        h = fp.read_text(); hl = h.lower()
        checks = [("Chart.js CDN","chart.js@4" in hl),("Viewport meta","viewport" in hl and "initial-scale" in hl),("Semantic header","<header" in hl),("Semantic main","<main" in hl),("Semantic footer","<footer" in hl),("KPI cards","kpi" in hl),("Canvas elements","<canvas" in hl),("Data embedding","const data" in hl or "const DATA" in h),("Design tokens","--" in h and "var(--" in h),("Color system",":root" in h)]
        passed = sum(1 for _,ok in checks if ok); total = len(checks)
        lines = [f"Dashboard validation: {passed}/{total}", ""]
        for n,ok in checks: lines.append(f"  {'✅' if ok else '❌'} {n}")
        return ToolResult(output="\n".join(lines))

class FetchDataSourceTool(Tool):
    name = "fetch_data_source"
    description = "Look up H Heuristics data sources: who-hap, iea-cooking, seforall, cca, world-bank, lancet, or all."
    parameters = {"type":"object","properties":{"source_name":{"type":"string","description":"Source key or 'all'."}},"required":["source_name"]}
    SOURCES = {
        "who-hap":{"name":"WHO Household Air Pollution Fact Sheet","url":"https://www.who.int/news-room/fact-sheets/detail/household-air-pollution-and-health","updated":"December 2025","key_metrics":["2.9M annual deaths","Disease breakdown","2.1B using polluting fuels"]},
        "iea-cooking":{"name":"IEA Clean Cooking in Africa 2026","url":"https://www.iea.org/reports/clean-cooking-in-africa-2026","updated":"2026","key_metrics":["$8B/yr investment need","$2.2B pledged","940M without access in SSA"]},
        "seforall":{"name":"SEforALL Chilling Prospects","url":"https://www.seforall.org/chilling-prospects-2023","updated":"2023","key_metrics":["1.12B at risk from lack of cooling","Regional breakdowns"]},
        "cca":{"name":"Clean Cooking Alliance","url":"https://cleancooking.org/","updated":"Ongoing","key_metrics":["Market intelligence","Carbon finance standards"]},
        "world-bank":{"name":"World Bank / ESMAP","url":"https://www.esmap.org/","updated":"Ongoing","key_metrics":["$500M Clean Cooking Fund","Energy access data"]},
        "lancet":{"name":"Lancet Countdown","url":"https://www.lancetcountdown.org/","updated":"2025","key_metrics":["546K heat-related deaths","85% increase in 65+ heat mortality"]},
    }
    def execute(self, source_name: str) -> ToolResult:
        if source_name == "all":
            lines = ["H Heuristics data sources:",""]
            for k,s in self.SOURCES.items():
                lines.append(f"  [{k}] {s['name']} ({s['updated']})")
                lines.append(f"       {s['url']}")
            return ToolResult(output="\n".join(lines))
        s = self.SOURCES.get(source_name.lower())
        if not s: return ToolResult(output=f"Unknown. Try: {', '.join(self.SOURCES)} or 'all'.", success=False)
        return ToolResult(output=f"{s['name']}\n  URL: {s['url']}\n  Updated: {s['updated']}\n  Key metrics: {', '.join(s['key_metrics'])}")

class MarketSizingTool(Tool):
    name = "market_sizing"
    description = "TAM estimates: electric-cooking, efficient-cooling, carbon-finance, payg-energy, or all."
    parameters = {"type":"object","properties":{"sector":{"type":"string","description":"Sector to size."}},"required":["sector"]}
    SIZING = {
        "electric-cooking":{"tam":"~800M households without clean cooking","market":"$8-15B annual appliance market","cagr":"25-40% in early-adopter markets","drivers":["Falling solar+battery costs","Carbon finance reducing cost 30-50%","LPG subsidy fatigue driving electric transition"]},
        "efficient-cooling":{"tam":"~1.1B at high risk from lack of cooling","market":"10 units sold/second; stock tripling by 2050","cagr":"8% HFC growth","drivers":["Rising temperatures+urbanization","Kigali Amendment phase-down","Solar-direct DC cooling"]},
        "carbon-finance":{"tam":"$15-30B/year at $10-20/tonne","market":"$3-8/tonne typical credit price","cagr":"Growing with CORSIA/Article 6 demand","drivers":["Gold Standard/Verra methodologies","Compliance market demand","Corporate net-zero commitments"]},
        "payg-energy":{"tam":"~500M off-grid households","market":"10-15M PAYG solar systems deployed","cagr":"15-25% in SSA","drivers":["M-KOPA/d.light/Sun King at scale","Smartphone+ mobile money","Expanding to productive use"]},
    }
    def execute(self, sector: str) -> ToolResult:
        if sector == "all":
            lines = ["Market Sizing Overview:",""]
            for k,d in self.SIZING.items():
                lines.append(f"  {k.replace('-',' ').title()}: {d['tam']} | {d['market']}")
            return ToolResult(output="\n".join(lines))
        d = self.SIZING.get(sector.lower())
        if not d: return ToolResult(output=f"Unknown. Try: {', '.join(self.SIZING)} or 'all'.", success=False)
        lines = [f"{sector.replace('-',' ').title()} — Market Sizing","",f"TAM: {d['tam']}",f"Market: {d['market']}",f"CAGR: {d['cagr']}","","Key drivers:"]
        for dr in d['drivers']: lines.append(f"  • {dr}")
        return ToolResult(output="\n".join(lines))

def register(registry):
    registry.register(ValidateDashboardTool())
    registry.register(FetchDataSourceTool())
    registry.register(MarketSizingTool())
    return registry
