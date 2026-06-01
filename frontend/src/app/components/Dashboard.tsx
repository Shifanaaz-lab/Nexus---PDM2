import { motion, AnimatePresence } from "motion/react";
import {
  Activity,
  AlertTriangle,
  Bell,
  User,
  Database,
  Radio,
  TrendingUp,
  BarChart3,
  Settings,
  Home,
  Zap,
  Shield,
  Wifi,
  CheckCircle2,
  Download,
  DollarSign,
  FileText,
  Filter,
  Calendar,
  ChevronDown,
  X,
  Search,
  Clock,
  TrendingDown,
  Maximize2,
  RefreshCw,
  Wrench,
  AlertOctagon,
  CircleDot,
  PieChart,
  Layout,
  Server,
  Thermometer,
  Gauge,
  XCircle,
  LogOut,
  Timer,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router";
import { clearSession, isSessionExpiringSoon, getSessionTimeRemaining, extendSession, getCurrentUser, formatTimeRemaining } from "../utils/sessionManager";
import { LineChart, Line, ComposedChart, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart as RPieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts";


const machineTypes = [
  { id: "turbines", name: "Gas Turbines", count: 12, icon: "⚡", criticality: "critical" },
  { id: "pumps", name: "Centrifugal Pumps", count: 24, icon: "🔄", criticality: "standard" },
  { id: "compressors", name: "Air Compressors", count: 18, icon: "💨", criticality: "standard" },
  { id: "generators", name: "Power Generators", count: 8, icon: "⚙️", criticality: "critical" },
  { id: "motors", name: "Electric Motors", count: 36, icon: "🔌", criticality: "standard" },
];

const timeRanges = [
  { id: "1h", label: "Last Hour" },
  { id: "24h", label: "24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "custom", label: "Custom Range" },
];

// AI Insights are now generated dynamically in Dashboard state



const defaultAnalyticsData = [
  { name: "Jan", failures: 4, predictions: 6, accuracy: 92, lead_time: 14.2, lead_time_unit: "days" },
  { name: "Feb", failures: 2, predictions: 3, accuracy: 95, lead_time: 11.8, lead_time_unit: "days" },
  { name: "Mar", failures: 5, predictions: 7, accuracy: 89, lead_time: 9.5,  lead_time_unit: "days" },
  { name: "Apr", failures: 1, predictions: 2, accuracy: 98, lead_time: 18.3, lead_time_unit: "days" },
];

const COLORS = ['#ef4444', '#f97316', '#22c55e', '#3b82f6'];

type TelemetryPoint = {
  time: string | number;
  temperature: number;
  pressure: number;
  vibration: number;
};

/** Client-side series so the chart never renders empty if the API omits or truncates telemetry. */
function buildLocalFallbackTelemetry(): TelemetryPoint[] {
  const now = new Date();
  return Array.from({ length: 30 }, (_, i) => ({
    time: new Date(now.getTime() - (29 - i) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    temperature: 120 + 15 * Math.sin(i * 0.2),
    pressure: 150 + 20 * Math.cos(i * 0.15),
    vibration: 15 + 8 * Math.sin(i * 0.25),
  }));
}

type EngineData = {
  id: string;
  health: number;
  status: "critical" | "warning" | "healthy";
  rul: number;
  location?: string;
  temp?: number;
  pressure?: number;
  vibration?: number;
  maintenance_status?: "scheduled" | "in-progress" | null;
};

type AlertData = {
  id: number;
  severity: "critical" | "warning" | "info";
  engine: string;
  message: string;
  time: string;
  acknowledged: boolean;
};

type FleetData = {
  active_engines: number;
  warning_count: number;
  critical_count: number;
};

type ApiData = {
  fleet?: FleetData;
  alerts?: AlertData[];
  engine_grid?: Array<{ id: string; risk: number; rul: number }>;
  analytics?: {
    metrics: {
      avg_risk: number;
      avg_health: number;
      critical_count: number;
      accuracy: number;
      false_positive: number;
      detection_rate: number;
    };
    distribution: {
      healthy: number;
      warning: number;
      critical: number;
    };
    timeline: Array<{
      name: string;
      failures: number;
      predictions: number;
      accuracy: number;
      lead_time?: number;
      lead_time_unit?: string;
    }>;
  };
  latest_records?: any[];
};

function getApiBaseUrl(): string {
  if (typeof window === "undefined") return "http://localhost:8001";
  
  // 1. Check if VITE_API_URL is injected by Vite at build time
  const envUrl = (import.meta.env as any).VITE_API_URL;
  if (envUrl && !envUrl.includes("<YOUR_ID>") && envUrl.startsWith("http")) {
    return envUrl;
  }

  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://localhost:8001";
  }

  // 2. Dynamic Render Blueprint domain mapping
  if (host.includes("predictive-maintenance-frontend")) {
    const protocol = window.location.protocol;
    const derivedHost = host.replace("predictive-maintenance-frontend", "predictive-maintenance-api");
    return `${protocol}//${derivedHost}`;
  }

  // Fallback
  return "https://predictive-maintenance-api.onrender.com";
}

function getEngineRangeForMachineTypeId(machineType: string): { start: number; end: number } {
  switch (machineType) {
    case "turbines": return { start: 1, end: 10 };
    case "compressors": return { start: 11, end: 22 };
    case "pumps": return { start: 23, end: 37 };
    case "generators": return { start: 38, end: 43 };
    case "motors": return { start: 44, end: 48 };
    default: return { start: 1, end: 48 };
  }
}

function normalizeAlert(raw: unknown): AlertData | null {
  if (raw == null || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const idRaw = o.id;
  const id = typeof idRaw === "number" ? idRaw : parseInt(String(idRaw ?? ""), 10);
  if (Number.isNaN(id)) return null;

  let severity: AlertData["severity"] = "warning";
  if (o.severity === "critical" || o.severity === "warning" || o.severity === "info") {
    severity = o.severity;
  }

  let engine = typeof o.engine === "string" ? o.engine : "";
  const msg = String(o.message ?? "");
  if (!engine) {
    const m = msg.match(/E-\d+/);
    engine = m ? m[0] : "Unknown";
  }

  return {
    id,
    severity,
    engine,
    message: msg,
    time: String(o.time ?? ""),
    acknowledged: Boolean(o.acknowledged),
  };
}

type MaintenanceTask = {
  id: number;
  engine: string;
  task: string;
  date: string;
  priority: "high" | "medium" | "low";
  status: "suggested" | "scheduled" | "in-progress" | "completed" | "dismissed";
  auto_scheduled?: boolean;
  suggestion_rule?: string;
  progress_ticks?: number;
  cost_saved?: number;
  pre_service?: {
    health: number;
    temp: number;
    pressure: number;
    vibration: number;
    rul: number;
  };
  post_service?: {
    health: number;
    temp: number;
    pressure: number;
    vibration: number;
    rul: number;
  };
};

function parseMaintenanceTask(raw: unknown): MaintenanceTask | null {
  if (raw == null || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const idRaw = o.id;
  const id = typeof idRaw === "number" ? idRaw : parseInt(String(idRaw ?? ""), 10);
  if (Number.isNaN(id)) return null;
  const engine = String(o.engine ?? "").trim() || "E-000";
  const task = String(o.task ?? "").trim() || "Untitled task";
  const date = String(o.date ?? "").trim();
  const st = String(o.status ?? "scheduled").toLowerCase();
  const status: MaintenanceTask["status"] =
    st === "completed" || st === "in-progress" || st === "scheduled" || st === "suggested" || st === "dismissed"
      ? (st as MaintenanceTask["status"])
      : "scheduled";
  const pr = String(o.priority ?? "medium").toLowerCase();
  const priority: MaintenanceTask["priority"] =
    pr === "high" || pr === "medium" || pr === "low" ? pr : "medium";
  const suggestion_rule = typeof o.suggestion_rule === "string" ? o.suggestion_rule : undefined;
  return {
    id,
    engine,
    task,
    date,
    priority,
    status,
    auto_scheduled: Boolean(o.auto_scheduled),
    suggestion_rule,
    progress_ticks: typeof o.progress_ticks === "number" ? o.progress_ticks : undefined,
    cost_saved: typeof o.cost_saved === "number" ? o.cost_saved : undefined,
    pre_service: o.pre_service ? (o.pre_service as any) : undefined,
    post_service: o.post_service ? (o.post_service as any) : undefined,
  };
}

function parseMaintenanceTaskList(raw: unknown): MaintenanceTask[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map(parseMaintenanceTask)
    .filter((x): x is MaintenanceTask => x !== null)
    .filter((x) => x.status !== "dismissed")  // hide dismissed suggestions from the UI
    .sort((a, b) => b.id - a.id);
}

/** Same risk→health→severity rules as engine cards when backend sends empty alerts[]. */
function alertsFromEngineGridForMachine(
  engineGrid: unknown,
  machineTypeId: string,
  limit = 12
): AlertData[] {
  if (!Array.isArray(engineGrid)) return [];
  const range = getEngineRangeForMachineTypeId(machineTypeId);
  const scored: { risk: number; alert: AlertData }[] = [];

  for (const raw of engineGrid) {
    if (raw == null || typeof raw !== "object") continue;
    const row = raw as { id?: string; risk?: number };
    const idStr = row.id ?? "";
    const match = idStr.match(/(\d+)/);
    if (!match) continue;
    const engineNum = parseInt(match[1], 10);
    if (Number.isNaN(engineNum) || engineNum < range.start || engineNum > range.end) continue;

    const risk = typeof row.risk === "number" ? row.risk : 0;
    const health = Math.round(Math.max(0, Math.min(100, (1 - risk) * 100)));
    if (health > 70) continue;

    const severity: AlertData["severity"] = health <= 50 ? "critical" : "warning";
    scored.push({
      risk,
      alert: {
        id: engineNum,
        severity,
        engine: idStr || `E-${String(engineNum).padStart(3, "0")}`,
        message: `Risk level ${risk.toFixed(2)} detected`,
        time: "Live",
        acknowledged: false,
      },
    });
  }

  scored.sort((a, b) => b.risk - a.risk);
  return scored.slice(0, limit).map((s) => s.alert);
}

export function Dashboard() {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [telemetryData, setTelemetryData] = useState<TelemetryPoint[]>([]);
  const [apiData, setApiData] = useState<ApiData>({});
  const [fleetData, setFleetData] = useState<EngineData[]>([]);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [activeNav, setActiveNav] = useState("dashboard");
  const [selectedMachine, setSelectedMachine] = useState(machineTypes[0]);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRanges[1]);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [analyticsData, setAnalyticsData] = useState<any[]>(defaultAnalyticsData);
  const [dynamicInsights, setDynamicInsights] = useState<{ id: number; icon: string; text: string; time: string; type: string }[]>([]);
  const [showMachineDropdown, setShowMachineDropdown] = useState(false);
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [alertSeverityFilter, setAlertSeverityFilter] = useState<'all' | 'critical' | 'warning' | 'unacknowledged'>('all');
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState<any>(null);
  const [showAlertPanel, setShowAlertPanel] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSessionWarning, setShowSessionWarning] = useState(false);
  const [sessionTimeRemaining, setSessionTimeRemaining] = useState(0);
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const [loadingStates, setLoadingStates] = useState<{ [key: string]: boolean }>({});
  const [notifications, setNotifications] = useState<{ id: string; type: 'success' | 'error'; message: string }[]>([]);
  /** When set, detailed diagnostics panel is open for this engine id — metrics sync from live fleetData each poll. */
  const [detailPanelEngineId, setDetailPanelEngineId] = useState<string | null>(null);
  const [engineDetails, setEngineDetails] = useState<any>(null);
  const [engineTelemetryData, setEngineTelemetryData] = useState<TelemetryPoint[]>([]);
  const [selectedReportFormat, setSelectedReportFormat] = useState<'pdf' | 'excel' | 'csv'>('pdf');
  const [maintenanceHistory, setMaintenanceHistory] = useState<MaintenanceTask[]>([]);
  const [showCreateMaintenanceModal, setShowCreateMaintenanceModal] = useState(false);
  const [newMaintenanceEngine, setNewMaintenanceEngine] = useState('');
  const [newMaintenanceTask, setNewMaintenanceTask] = useState('');
  const [newMaintenanceDate, setNewMaintenanceDate] = useState('');
  const [newMaintenancePriority, setNewMaintenancePriority] = useState<'high' | 'medium' | 'low'>('medium');
  const [selectedMaintenanceTask, setSelectedMaintenanceTask] = useState<MaintenanceTask | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Find active engine to represent on the Failure Timeline (default to the most critical engine in the fleet if none selected)
  const activeTimelineEngineId = detailPanelEngineId || (fleetData.length > 0 ? [...fleetData].sort((a, b) => a.health - b.health)[0].id : null);
  const activeTimelineEngine = fleetData.find(e => e.id === activeTimelineEngineId);

  const stableActive = activeTimelineEngine ? activeTimelineEngine.health >= 70 : true;
  const degradingActive = activeTimelineEngine ? (activeTimelineEngine.health < 70 && activeTimelineEngine.health >= 50) : false;
  const criticalActive = activeTimelineEngine ? activeTimelineEngine.health < 50 : false;
  
  const activeColor = stableActive ? "emerald" : degradingActive ? "amber" : "red";
  const activeColorRgb = stableActive ? "16, 185, 129" : degradingActive ? "245, 158, 11" : "239, 68, 68";

  const timelineStages = [
    { label: "Stable", sublabel: "Nominal operation", color: "emerald", active: stableActive },
    { label: "Degrading", sublabel: "Performance decline", color: "amber", active: degradingActive },
    { label: "Critical", sublabel: "Imminent failure", color: "red", active: criticalActive },
  ];

  const alertsRef = useRef<AlertData[]>([]);
  useEffect(() => {
    alertsRef.current = alerts;
  }, [alerts]);

  const refreshMaintenanceHistory = useCallback(async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      const maintenanceRes = await fetch(`${apiBaseUrl}/api/maintenance_history`);
      const maintenanceData = await maintenanceRes.json().catch(() => ({}));
      if (!maintenanceRes.ok || maintenanceData.status !== "success") {
        console.error("Maintenance history request failed:", maintenanceData);
        return;
      }
      setMaintenanceHistory(parseMaintenanceTaskList(maintenanceData.maintenance));
    } catch (err) {
      console.error("Maintenance API error:", err);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const fetchData = useCallback(async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      
      const apiUrl = `${apiBaseUrl}/api/telemetry?machine_type=${selectedMachine.id}&time_range=${selectedTimeRange.id}&q=${debouncedSearch}`;
      const analyticsUrl = `${apiBaseUrl}/api/analytics?machine_type=${selectedMachine.id}&time_range=${selectedTimeRange.id}&q=${debouncedSearch}`;
      
      const [res, analyticsRes] = await Promise.all([
        fetch(apiUrl),
        fetch(analyticsUrl)
      ]);

      if (!res.ok || !analyticsRes.ok) {
        throw new Error(`API request failed: ${res.status} or ${analyticsRes.status}`);
      }
      
      const data = await res.json();
      const analyticsDataResponse = await analyticsRes.json();

      if (data.status !== "success") {
        console.error('API returned non-success status:', data);
        return;
      }

      // Process telemetry data (must be parallel arrays; tolerate missing / bad API shapes)
      const lines = data.telemetry_lines;
      const ts = lines?.timestamps;
      let formatted: TelemetryPoint[] = [];
      if (Array.isArray(ts) && ts.length > 0) {
        const s1 = Array.isArray(lines?.s1) ? lines!.s1! : [];
        const s2 = Array.isArray(lines?.s2) ? lines!.s2! : [];
        const s3 = Array.isArray(lines?.s3) ? lines!.s3! : [];
        formatted = ts.map((timeStr, i) => {
          const temperature = Number(s1[i]);
          const pressure = Number(s2[i]);
          const vibration = Number(s3[i]);
          return {
            time: timeStr,
            temperature: Number.isFinite(temperature) ? temperature : 0,
            pressure: Number.isFinite(pressure) ? pressure : 0,
            vibration: Number.isFinite(vibration) ? vibration : 0,
          };
        });
      }
      if (formatted.length < 2) {
        formatted = buildLocalFallbackTelemetry();
      }
      setTelemetryData(formatted);

      // Process engine grid data with machine type filtering
      if (data.engine_grid && Array.isArray(data.engine_grid)) {
        // Filter engines by selected machine type
        const filteredEngines = data.engine_grid.filter((engine: any) => {
          const engineId = parseInt(engine.id?.split('-')[1]);
          if (isNaN(engineId)) return true;
          
          const engineRange = getEngineRangeForMachineTypeId(selectedMachine.id);
          return engineId >= engineRange.start && engineId <= engineRange.end;
        });
        
        const processedEngines = filteredEngines.map((engine: any) => {
          const risk = typeof engine.risk === 'number' ? engine.risk : 0;
          const rul = typeof engine.rul === 'number' ? engine.rul : 0;
          const health = Math.round(Math.max(0, Math.min(100, (1 - risk) * 100)));
          let status: "critical" | "warning" | "healthy" = "healthy";
          if (health <= 50) status = "critical";
          else if (health <= 70) status = "warning";
          
          // Get real metrics from backend if available, otherwise use fallback
          let temp = typeof engine.temp === 'number' ? Math.round(engine.temp) : 70;
          let pressure = typeof engine.pressure === 'number' ? Math.round(engine.pressure) : 50;
          let vibration = typeof engine.vibration === 'number' ? Math.round(engine.vibration) : 40;
          
          return {
            id: engine.id || 'Unknown',
            health,
            status,
            rul,
            location: `Plant ${String.fromCharCode(65 + (parseInt((engine.id || 'E-001').split('-')[1]) % 3))}`,
            temp: temp, // Use real temperature from backend
            pressure: pressure, // Use real pressure from backend
            vibration: vibration, // Use real vibration from backend
            maintenance_status: engine.maintenance_status, // Map active maintenance status
            machineType: selectedMachine.id // Add machine type to engine data
          };
        });
        
        setFleetData(processedEngines);
      } else {
        setFleetData([]);
      }

      // Alerts: prefer backend alerts[] (normalized), else derive from engine_grid so the tab
      // matches orange engine cards (same health thresholds as the fleet view).
      let nextAlerts: AlertData[] = [];

      if (data.alerts && Array.isArray(data.alerts)) {
        const normalized = (data.alerts as any[])
          .map(normalizeAlert)
          .filter((a: AlertData | null): a is AlertData => a !== null);

        nextAlerts = normalized.filter((alert: AlertData) => {
          const engineMatch = alert.engine.match(/(\d+)/);
          if (engineMatch) {
            const alertEngineId = parseInt(engineMatch[1], 10);
            const engineRange = getEngineRangeForMachineTypeId(selectedMachine.id);
            return alertEngineId >= engineRange.start && alertEngineId <= engineRange.end;
          }
          const msgMatch = alert.message.match(/E-(\d+)/);
          if (msgMatch) {
            const alertEngineId = parseInt(msgMatch[1], 10);
            const engineRange = getEngineRangeForMachineTypeId(selectedMachine.id);
            return alertEngineId >= engineRange.start && alertEngineId <= engineRange.end;
          }
          return true;
        });
      }

      if (nextAlerts.length === 0 && data.engine_grid && Array.isArray(data.engine_grid)) {
        nextAlerts = alertsFromEngineGridForMachine(data.engine_grid, selectedMachine.id);
      }

      // Deduplicate alerts by engine ID to ensure one stable card per machine
      // Also merge with existing alerts to preserve 'id' (stops blinking) and 'acknowledged' status.
      const existingAlerts = alertsRef.current;
      const deduplicatedAlerts = Array.from(
        new Map(nextAlerts.map(a => [a.engine, a])).values()
      ).map(newAlert => {
        const existing = existingAlerts.find(ea => ea.engine === newAlert.engine);
        if (existing) {
          return {
            ...newAlert,
            id: existing.id,
            acknowledged: existing.acknowledged
          };
        }
        return newAlert;
      });

      // Process machine counts from API
      if (data.fleet?.machine_counts) {
        Object.entries(data.fleet.machine_counts).forEach(([id, count]) => {
          const mt = machineTypes.find(m => m.id === id);
          if (mt) mt.count = count as number;
        });
      }
      setAlerts(deduplicatedAlerts);
      alertsRef.current = deduplicatedAlerts;

      // Generate dynamic insights based on most critical engines
      const topInsights = deduplicatedAlerts.slice(0, 5).map((alert, i) => ({
        id: alert.id,
        icon: alert.severity === 'critical' ? 'alert' : 'check',
        text: `${alert.severity === 'critical' ? 'Urgent' : 'Maintenance'}: ${alert.engine} showing ${alert.message}`,
        time: alert.time,
        type: alert.severity === 'critical' ? 'warning' : 'success'
      }));
      setDynamicInsights(topInsights);

      // Update API status with error handling
      if (data && data.status === "success") {
        const combinedData = {
          ...data,
          analytics: analyticsDataResponse.status === "success" ? analyticsDataResponse : undefined
        };
        setApiData(combinedData);
        
        if (analyticsDataResponse.status === "success" && analyticsDataResponse.timeline) {
          setAnalyticsData(analyticsDataResponse.timeline);
        }
      } else {
        console.error("Invalid API response:", data);
        return;
      }

      await refreshMaintenanceHistory();
    } catch (err) {
      console.error("API error:", err);
    }
  }, [selectedMachine, selectedTimeRange, debouncedSearch, refreshMaintenanceHistory]);

  // Helper function to assign engines to machine types based on realistic specs
  const getMachineTypeForEngine = (engineId: number): string => {
    // Based on realistic equipment distribution
    if (engineId >= 1 && engineId <= 10) return "turbines";
    if (engineId >= 11 && engineId <= 22) return "compressors";
    if (engineId >= 23 && engineId <= 37) return "pumps";
    if (engineId >= 38 && engineId <= 43) return "generators";
    if (engineId >= 44 && engineId <= 48) return "motors";
    return "unknown";
  };

  // Helper function to get engine range for machine type
  const getEngineRangeForMachineType = (machineType: string): { start: number; end: number } =>
    getEngineRangeForMachineTypeId(machineType);

useEffect(() => {
  const timer = setInterval(() => {
    setCurrentTime(new Date());
  }, 1000);

  let cancelled = false;
  let timeoutId: ReturnType<typeof setTimeout>;

  const scheduleNext = () => {
    if (cancelled) return;
    const hasCriticalAlerts = alertsRef.current.some((alert) => alert.severity === "critical");
    const isCriticalMachine = selectedMachine.criticality === "critical";
    const pollingInterval = hasCriticalAlerts || isCriticalMachine ? 500 : 1000;
    timeoutId = setTimeout(async () => {
      if (cancelled) return;
      await fetchData();
      scheduleNext();
    }, pollingInterval);
  };

  fetchData();
  scheduleNext();

  return () => {
    cancelled = true;
    clearInterval(timer);
    clearTimeout(timeoutId);
  };
}, [selectedMachine, fetchData]);

  useEffect(() => {
    if (activeNav === "maintenance") {
      void refreshMaintenanceHistory();
    }
  }, [activeNav, refreshMaintenanceHistory]);

  useEffect(() => {
    if (detailPanelEngineId && apiData.latest_records) {
      const engineMatch = detailPanelEngineId.match(/(\d+)/);
      if (engineMatch) {
        const engineNum = parseInt(engineMatch[1], 10);
        const record = apiData.latest_records.find((r: any) => r.engine_id === engineNum);
        if (record) {
          setEngineTelemetryData(prev => {
            const timeStr = new Date(record.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            if (prev.length > 0 && prev[prev.length - 1].time === timeStr) return prev;
            
            const newPoint = {
              time: timeStr,
              temperature: record.features.s1,
              pressure: record.features.s2,
              vibration: record.features.s3
            };
            return [...prev, newPoint].slice(-30);
          });
        }
      }
    }
  }, [apiData, detailPanelEngineId]);

  const handleLogout = () => {
    clearSession();
    navigate("/");
  };

  const handleExtendSession = () => {
    extendSession();
    setShowSessionWarning(false);
  };

  // API Action Functions
  const acknowledgeAlert = async (alertId: number) => {
    const key = `ack-alert-${alertId}`;
    setLoadingStates(prev => ({ ...prev, [key]: true }));
    
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/acknowledge_alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId })
      });
      
      const payload = await response.json().catch(() => ({}));
      if (response.ok && payload.status === 'success') {
        setAlerts(prev => {
          const updated = prev.map(alert =>
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          );
          alertsRef.current = updated;
          return updated;
        });
        addNotification('success', `Alert ${alertId} acknowledged successfully`);
      } else {
        addNotification('error', 'Failed to acknowledge alert');
      }
    } catch (error) {
      addNotification('error', 'Network error while acknowledging alert');
    } finally {
      setLoadingStates(prev => ({ ...prev, [key]: false }));
    }
  };

  const openEngineDetails = async (engineId: string) => {
    setDetailPanelEngineId(engineId);
    const key = `engine-details-${engineId}`;
    setLoadingStates(prev => ({ ...prev, [key]: true }));

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/engine/${encodeURIComponent(engineId)}`);
      if (response.ok) {
        const data = await response.json();
        setEngineDetails(data);
        if (data.telemetry_history && Array.isArray(data.telemetry_history)) {
          setEngineTelemetryData(data.telemetry_history);
        }
        addNotification('success', `Loaded details for ${engineId}`);
      } else {
        addNotification('error', 'Failed to load engine details');
      }
    } catch (error) {
      addNotification('error', 'Network error while loading engine details');
    } finally {
      setLoadingStates(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    const key = 'manual-refresh';
    setLoadingStates(prev => ({ ...prev, [key]: true }));
    
    try {
      // Fetch main dashboard data (telemetry & analytics)
      await fetchData();
      
      // Fetch maintenance history
      await refreshMaintenanceHistory();
      
      // If a detailed engine panel is open, re-fetch its details and history too!
      if (detailPanelEngineId) {
        const response = await fetch(`${getApiBaseUrl()}/api/engine/${encodeURIComponent(detailPanelEngineId)}`);
        if (response.ok) {
          const data = await response.json();
          setEngineDetails(data);
          if (data.telemetry_history && Array.isArray(data.telemetry_history)) {
            setEngineTelemetryData(data.telemetry_history);
          }
        }
      }
      
      addNotification('success', 'Dashboard data successfully refreshed');
    } catch (error) {
      console.error('Error during manual refresh:', error);
      addNotification('error', 'Failed to refresh dashboard data');
    } finally {
      setTimeout(() => {
        setIsRefreshing(false);
        setLoadingStates(prev => ({ ...prev, [key]: false }));
      }, 600);
    }
  };

  const closeEngineDetails = () => {
    setDetailPanelEngineId(null);
    setEngineDetails(null);
    setEngineTelemetryData([]);
  };

  const scheduleMaintenance = async (
    engineId: string,
    task: string,
    date: string,
    priority: string
  ): Promise<boolean> => {
    const key = "schedule-maintenance";
    setLoadingStates((prev) => ({ ...prev, [key]: true }));
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/schedule_maintenance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          engine_id: engineId.trim(),
          task: task.trim(),
          date,
          priority,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || result.status !== "success") {
        const msg = typeof result.message === "string" ? result.message : "Failed to schedule maintenance";
        addNotification("error", msg);
        return false;
      }
      const created = parseMaintenanceTask(result.maintenance);
      if (created) {
        setMaintenanceHistory((prev) => {
          if (prev.some((m) => m.id === created.id)) return prev;
          return [created, ...prev].sort((a, b) => b.id - a.id);
        });
        addNotification("success", `Maintenance scheduled for ${created.engine}`);
      } else {
        await refreshMaintenanceHistory();
        addNotification("success", `Maintenance scheduled for ${engineId.trim()}`);
      }
      return true;
    } catch {
      addNotification("error", "Network error while scheduling maintenance");
      return false;
    } finally {
      setLoadingStates((prev) => ({ ...prev, [key]: false }));
    }
  };

  const handleCreateMaintenance = async () => {
    if (!newMaintenanceEngine.trim() || !newMaintenanceTask.trim() || !newMaintenanceDate) {
      addNotification("error", "Please fill in all required fields");
      return;
    }
    const ok = await scheduleMaintenance(
      newMaintenanceEngine,
      newMaintenanceTask,
      newMaintenanceDate,
      newMaintenancePriority
    );
    if (ok) {
      setShowCreateMaintenanceModal(false);
      setNewMaintenanceEngine("");
      setNewMaintenanceTask("");
      setNewMaintenanceDate("");
      setNewMaintenancePriority("medium");
    }
  };

  const maintenancePlannerAction = async (id: number, action: "confirm" | "dismiss") => {
    const key = `maint-action-${id}`;
    setLoadingStates((prev) => ({ ...prev, [key]: true }));
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/maintenance_action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, action }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || result.status !== "success") {
        const msg = typeof result.message === "string" ? result.message : "Action failed";
        addNotification("error", msg);
        return;
      }
      await refreshMaintenanceHistory();
      setSelectedMaintenanceTask(null);
      addNotification("success", action === "confirm" ? "Maintenance confirmed" : "Suggestion dismissed");
    } catch {
      addNotification("error", "Network error");
    } finally {
      setLoadingStates((prev) => ({ ...prev, [key]: false }));
    }
  };

  const markAllAlertsRead = async () => {
    setLoadingStates(prev => ({ ...prev, 'mark-all-read': true }));
    
    try {
      const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged);
      const base = getApiBaseUrl();
      let successful = 0;

      for (const alert of unacknowledgedAlerts) {
        try {
          const response = await fetch(`${base}/api/acknowledge_alert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: alert.id })
          });
          const payload = await response.json().catch(() => ({}));
          if (response.ok && payload.status === 'success') {
            successful++;
            setAlerts(prev => {
              const next = prev.map(a =>
                a.id === alert.id ? { ...a, acknowledged: true } : a
              );
              alertsRef.current = next;
              return next;
            });
          }
        } catch {
          /* continue with next alert */
        }
      }

      if (successful > 0) {
        addNotification('success', `${successful} alerts acknowledged successfully`);
      }

      if (unacknowledgedAlerts.length > 0 && successful < unacknowledgedAlerts.length) {
        addNotification('error', `${unacknowledgedAlerts.length - successful} alerts failed to acknowledge`);
      }
    } catch (error) {
      addNotification('error', 'Failed to acknowledge all alerts');
    } finally {
      setLoadingStates(prev => ({ ...prev, 'mark-all-read': false }));
    }
  };

  const clearAlert = async (alertId: number) => {
    const key = `clear-alert-${alertId}`;
    setLoadingStates(prev => ({ ...prev, [key]: true }));
    
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/clear_alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId })
      });
      
      const payload = await response.json().catch(() => ({}));
      if (response.ok && payload.status === 'success') {
        setAlerts(prev => {
          const next = prev.filter(alert => alert.id !== alertId);
          alertsRef.current = next;
          return next;
        });
        addNotification('success', `Alert ${alertId} cleared`);
      } else {
        addNotification('error', 'Failed to clear alert');
      }
    } catch (error) {
      addNotification('error', 'Network error while clearing alert');
    } finally {
      setLoadingStates(prev => ({ ...prev, [key]: false }));
    }
  };

  const clearAllAlerts = async () => {
    setLoadingStates(prev => ({ ...prev, 'clear-all': true }));
    
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/clear_all_alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const payload = await response.json().catch(() => ({}));
      if (response.ok && payload.status === 'success') {
        setAlerts([]);
        alertsRef.current = [];
        addNotification('success', 'All alerts cleared successfully');
      } else {
        addNotification('error', 'Failed to clear alerts');
      }
    } catch (error) {
      addNotification('error', 'Network error while clearing alerts');
    } finally {
      setLoadingStates(prev => ({ ...prev, 'clear-all': false }));
    }
  };

  const addNotification = (type: 'success' | 'error', message: string) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const navItems = [
    { id: "dashboard", icon: Home, label: "Dashboard" },
    { id: "engines", icon: Radio, label: "Engines" },
    { id: "insights", icon: Zap, label: "AI Insights" },
    { id: "alerts", icon: Bell, label: "Alerts" },
    { id: "maintenance", icon: Wrench, label: "Maintenance" },
    { id: "analytics", icon: BarChart3, label: "Analytics" },
  ];

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    
    try {
      // Generate report data
      const reportData = {
        timestamp: new Date().toISOString(),
        fleet: {
          total_engines: fleetData.length,
          healthy: fleetData.filter(e => e.status === 'healthy').length,
          warning: fleetData.filter(e => e.status === 'warning').length,
          critical: fleetData.filter(e => e.status === 'critical').length
        },
        engines: fleetData.map(engine => ({
          id: engine.id,
          health: engine.health,
          rul: engine.rul,
          status: engine.status,
          location: engine.location
        })),
        alerts: alerts,
        telemetry: telemetryData.slice(-10) // Last 10 data points
      };
      
      let filename, mimeType, content;
      
      if (selectedReportFormat === 'csv') {
        // Generate CSV
        const csvContent = [
          'Report Type: Fleet Analysis',
          `Generated: ${new Date().toLocaleString()}`,
          '',
          'Engine ID,Health (%),RUL (hours),Status,Location',
          ...reportData.engines.map(engine => 
            `${engine.id},${engine.health},${engine.rul},${engine.status},${engine.location}`
          ),
          '',
          'Alerts',
          'ID,Severity,Engine,Message,Time,Acknowledged',
          ...reportData.alerts.map(alert => 
            `${alert.id},${alert.severity},${alert.engine},"${alert.message}",${alert.time},${alert.acknowledged}`
          )
        ].join('\n');
        
        filename = `fleet_report_${Date.now()}.csv`;
        mimeType = 'text/csv';
        content = csvContent;
        
      } else if (selectedReportFormat === 'excel') {
        // Generate Excel-like TSV (tab-separated values)
        const tsvContent = [
          'Fleet Analysis Report\t' + new Date().toLocaleString(),
          '',
          'Engine ID\tHealth (%)\tRUL (hours)\tStatus\tLocation',
          ...reportData.engines.map(engine => 
            `${engine.id}\t${engine.health}\t${engine.rul}\t${engine.status}\t${engine.location}`
          ),
          '',
          'Alerts',
          'ID\tSeverity\tEngine\tMessage\tTime\tAcknowledged',
          ...reportData.alerts.map(alert => 
            `${alert.id}\t${alert.severity}\t${alert.engine}\t"${alert.message}"\t${alert.time}\t${alert.acknowledged}`
          )
        ].join('\n');
        
        filename = `fleet_report_${Date.now()}.tsv`;
        mimeType = 'text/tab-separated-values';
        content = tsvContent;
        
      } else {
        // Generate PDF-like text report
        const pdfContent = [
          'FLEET ANALYSIS REPORT',
          '=' .repeat(50),
          `Generated: ${new Date().toLocaleString()}`,
          '',
          'FLEET OVERVIEW',
          '-' .repeat(30),
          `Total Engines: ${reportData.fleet.total_engines}`,
          `Healthy: ${reportData.fleet.healthy}`,
          `Warning: ${reportData.fleet.warning}`,
          `Critical: ${reportData.fleet.critical}`,
          '',
          'ENGINE DETAILS',
          '-' .repeat(30),
          ...reportData.engines.map(engine => 
            `${engine.id}: Health ${engine.health}%, RUL ${engine.rul}h, Status: ${engine.status}`
          ),
          '',
          'ACTIVE ALERTS',
          '-' .repeat(30),
          ...reportData.alerts.map(alert => 
            `[${alert.severity.toUpperCase()}] ${alert.engine}: ${alert.message} (${alert.time})`
          )
        ].join('\n');
        
        filename = `fleet_report_${Date.now()}.txt`;
        mimeType = 'text/plain';
        content = pdfContent;
      }
      
      // Create and download file
      const blob = new Blob([content], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      addNotification('success', `Report generated and downloaded as ${filename}`);
      setShowReportModal(false);
      
    } catch (error) {
      addNotification('error', 'Failed to generate report');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const displayedFleet = fleetData.filter(engine => 
    engine.id.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (engine.location && engine.location.toLowerCase().includes(searchQuery.toLowerCase())) ||
    engine.status.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (engine.maintenance_status && engine.maintenance_status.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const renderDashboardView = () => {
    return (
    <div className="space-y-6">
      {/* Top Section - Telemetry & Engine Network */}
      <div className="grid grid-cols-3 gap-6">
        {/* Real-Time Telemetry */}
        <div className="col-span-2 backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">REAL-TIME TELEMETRY</h3>
              <p className="text-xs text-gray-400">Streaming sensor data pipeline</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-xs text-gray-400">Temperature</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-xs text-gray-400">Pressure</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <span className="text-xs text-gray-400">Vibration</span>
              </div>
            </div>
          </div>

          <div className="h-48 min-h-[12rem] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.15)" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: "#9ca3af", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "rgba(148, 163, 184, 0.25)" }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "rgba(148, 163, 184, 0.25)" }} domain={["auto", "auto"]} width={42} />
                <Tooltip
                  isAnimationActive={false}
                  contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                  labelFormatter={(v) => `Time: ${v}`}
                />
                <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
                <Line type="monotone" dataKey="pressure" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
                <Line type="monotone" dataKey="vibration" stroke="#a855f7" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between mt-4 text-xs text-gray-400">
            <span>Last updated: 0.2s ago</span>
            <span className="text-red-400">⚠ Anomaly Detected</span>
          </div>
        </div>

        {/* Engine Network */}
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-white mb-1">ENGINE NETWORK</h3>
            <p className="text-xs text-gray-400">Digital twin topology</p>
          </div>

          <div className="relative h-48 flex items-center justify-center">
            <motion.div
              className="absolute w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500/30 to-blue-500/30 border-2 border-cyan-400 flex items-center justify-center"
              animate={{
                boxShadow: ["0 0 20px rgba(6, 182, 212, 0.5)", "0 0 40px rgba(6, 182, 212, 0.8)", "0 0 20px rgba(6, 182, 212, 0.5)"],
              }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Database className="w-6 h-6 text-cyan-400" />
            </motion.div>

            {[0, 60, 120, 180, 240, 300].map((angle, index) => {
              const radius = 80;
              const x = Math.cos((angle * Math.PI) / 180) * radius;
              const y = Math.sin((angle * Math.PI) / 180) * radius;
              const engine = fleetData[index];
              const status = engine ? engine.status : "healthy";

              return (
                <motion.div
                  key={angle}
                  className={`absolute w-10 h-10 rounded-full border-2 flex items-center justify-center cursor-pointer ${
                    status === "critical" ? "bg-red-500/20 border-red-500" :
                    status === "warning" ? "bg-orange-500/20 border-orange-500" :
                    "bg-green-500/20 border-green-500"
                  }`}
                  style={{
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                    transform: "translate(-50%, -50%)",
                  }}
                  animate={status === "critical" ? {
                    boxShadow: ["0 0 10px rgba(239, 68, 68, 0.5)", "0 0 25px rgba(239, 68, 68, 0.8)", "0 0 10px rgba(239, 68, 68, 0.5)"],
                  } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                  whileHover={{ scale: 1.2 }}
                >
                  <Radio className="w-4 h-4 text-white" />
                </motion.div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs text-gray-400">{fleetData.filter(e => e.status === "healthy").length} Healthy</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <span className="text-xs text-gray-400">{fleetData.filter(e => e.status === "warning").length} Warning</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-xs text-gray-400">{fleetData.filter(e => e.status === "critical").length} Critical</span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Pipeline */}
      <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Data Pipeline</h3>
            <p className="text-xs text-gray-400">End-to-end processing architecture</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/30">
            <motion.div className="w-2 h-2 rounded-full bg-green-400" animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.5, repeat: Infinity }} />
            <span className="text-xs text-green-400 font-medium">LIVE</span>
          </div>
        </div>

        <div className="grid grid-cols-5 gap-6">
          {[
            { icon: Wifi, label: "Sensors", value: fleetData.length > 0 ? `${fleetData.length * 100}/s` : "0/s", color: "cyan" },
            { icon: Activity, label: "Streaming", value: "32ms", color: "blue" },
            { icon: Database, label: "MongoDB", value: "847B", color: "green" },
            { icon: Zap, label: "AI Model", value: null, color: "purple" },
            { icon: BarChart3, label: "Prediction", value: "99.6%", color: "orange" },
          ].map((item, index) => {
            const Icon = item.icon;
            return (
              <div key={index} className="relative">
                <div className="flex flex-col items-center">
                  <motion.div
                    className={`w-16 h-16 rounded-xl bg-${item.color}-500/10 border border-${item.color}-500/30 flex items-center justify-center mb-3`}
                    animate={{ boxShadow: [`0 0 10px rgba(6, 182, 212, 0.2)`, `0 0 20px rgba(6, 182, 212, 0.4)`, `0 0 10px rgba(6, 182, 212, 0.2)`] }}
                    transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
                  >
                    <Icon className={`w-6 h-6 text-${item.color}-400`} />
                  </motion.div>
                  <span className="text-xs text-gray-400 mb-1">{item.label}</span>
                  {item.value && <span className={`text-sm font-bold text-${item.color}-400`}>{item.value}</span>}
                </div>
                {index < 4 && (
                  <motion.div
                    className="absolute top-8 left-[calc(100%+0.5rem)] w-6 h-0.5 bg-gradient-to-r from-cyan-500/50 to-cyan-500/10"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-3 gap-6">
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-cyan-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI INSIGHTS FEED</h3>
              <p className="text-xs text-gray-400">Real-time intelligence stream</p>
            </div>
          </div>
          <div className="space-y-2">
            {dynamicInsights.map((insight, index) => (
              <motion.div
                key={insight.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer"
              >
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-gray-300 mb-1">{insight.text}</p>
                    <span className="text-xs text-gray-500">{insight.time}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">FAILURE TIMELINE</h3>
              <p className="text-xs text-gray-400">Degradation progression</p>
            </div>
          </div>
          <div className="relative py-4">
            {timelineStages.map((stage, index) => (
              <div key={index} className="relative flex items-center gap-4 mb-6 last:mb-0">
                <motion.div
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center ${
                    stage.active ? `bg-${stage.color}-500/20 border-${stage.color}-500` : "bg-gray-500/10 border-gray-500"
                  }`}
                  animate={stage.active ? {
                    boxShadow: [`0 0 10px rgba(${activeColorRgb}, 0.5)`, `0 0 20px rgba(${activeColorRgb}, 0.8)`, `0 0 10px rgba(${activeColorRgb}, 0.5)`]
                  } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {stage.active && <div className={`w-3 h-3 rounded-full bg-${stage.color}-500`} />}
                </motion.div>
                <div>
                  <div className={`text-sm font-bold ${stage.active ? `text-${stage.color}-400` : "text-gray-500"}`}>{stage.label}</div>
                  <div className="text-xs text-gray-500">{stage.sublabel}</div>
                </div>
                {index < 2 && <div className="absolute left-4 top-10 w-0.5 h-6 bg-gradient-to-b from-gray-500/50 to-transparent" />}
              </div>
            ))}
            <div className={`mt-4 p-3 rounded-lg border bg-${activeColor}-500/10 border-${activeColor}-500/30`}>
              <p className={`text-xs text-${activeColor}-400 font-semibold`}>
                {activeTimelineEngine ? `${activeTimelineEngine.id}: Predicted to ${activeTimelineEngine.rul.toFixed(1)}h Remaining` : "No active engine data"}
              </p>
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">FLEET HEALTH</h3>
              <p className="text-xs text-gray-400">Remaining useful life</p>
            </div>
          </div>
          <div className="mb-6">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-cyan-400">
                {fleetData.length > 0 ? Math.round(fleetData.reduce((acc, engine) => acc + engine.health, 0) / fleetData.length) : 0}%
              </span>
              <span className="text-sm text-gray-400">Overall Health</span>
            </div>
          </div>
          <div className="space-y-4">
            {/* Fleet Statistics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {fleetData.filter(e => e.status === "healthy").length}
                </div>
                <div className="text-xs text-gray-400">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400">
                  {fleetData.filter(e => e.status === "warning").length}
                </div>
                <div className="text-xs text-gray-400">Warning</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">
                  {fleetData.filter(e => e.status === "critical").length}
                </div>
                <div className="text-xs text-gray-400">Critical</div>
              </div>
            </div>

            {/* Health Distribution Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Fleet Distribution</span>
                <span>{fleetData.length} Total Units</span>
              </div>
              <div className="h-3 bg-gray-700/50 rounded-full overflow-hidden flex">
                <div 
                  className="bg-green-500 transition-all duration-500"
                  style={{ width: `${fleetData.length > 0 ? (fleetData.filter(e => e.status === "healthy").length / fleetData.length) * 100 : 0}%` }}
                />
                <div 
                  className="bg-orange-500 transition-all duration-500"
                  style={{ width: `${fleetData.length > 0 ? (fleetData.filter(e => e.status === "warning").length / fleetData.length) * 100 : 0}%` }}
                />
                <div 
                  className="bg-red-500 transition-all duration-500"
                  style={{ width: `${fleetData.length > 0 ? (fleetData.filter(e => e.status === "critical").length / fleetData.length) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Risk Indicators */}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs text-gray-400">Avg Risk Level</span>
                </div>
                <div className="text-lg font-bold text-cyan-400">
                  {fleetData.length > 0 ? (fleetData.reduce((acc, e) => acc + (100 - e.health), 0) / fleetData.length / 100).toFixed(2) : '0.00'}
                </div>
              </div>
              <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs text-gray-400">Avg RUL</span>
                </div>
                <div className="text-lg font-bold text-cyan-400">
                  {fleetData.length > 0 ? Math.round(fleetData.reduce((acc, e) => acc + e.rul, 0) / fleetData.length) : 0}h
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    );
  };

  const renderEnginesView = () => {
    const detailLive =
      detailPanelEngineId != null
        ? fleetData.find((e) => e.id === detailPanelEngineId)
        : undefined;
    const detailHealth = detailLive?.health ?? engineDetails?.health;
    const detailRul = detailLive?.rul ?? engineDetails?.rul;
    const detailTemp = detailLive?.temp ?? engineDetails?.temp;
    const detailPressure = detailLive?.pressure ?? engineDetails?.pressure;
    const detailVibration = detailLive?.vibration ?? engineDetails?.vibration;
    const detailTitleId = detailLive?.id ?? engineDetails?.id ?? detailPanelEngineId ?? "Unknown";

    return (
    <div className="space-y-6">
      <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Engine Fleet Overview</h3>
        <div className="grid grid-cols-4 gap-4">
          {displayedFleet.map((engine) => (
            <motion.div
              key={engine.id}
              whileHover={{ scale: 1.02 }}
              onClick={() => openEngineDetails(engine.id)}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all relative overflow-hidden ${
                engine.maintenance_status === "in-progress" ? "bg-cyan-500/10 border-cyan-400 border-dashed animate-pulse" :
                engine.maintenance_status === "scheduled" ? "bg-orange-500/10 border-orange-400 border-dashed animate-pulse" :
                engine.status === "critical" ? "bg-red-500/10 border-red-500/50" :
                engine.status === "warning" ? "bg-orange-500/10 border-orange-500/50" :
                "bg-green-500/10 border-green-500/50"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white">{engine.id}</span>
                  {engine.maintenance_status && (
                    <Wrench className={`w-4 h-4 ${engine.maintenance_status === "in-progress" ? "text-cyan-400" : "text-orange-400"}`} />
                  )}
                </div>
                {engine.maintenance_status ? (
                  <span className={`text-[10px] uppercase font-bold tracking-wide px-2 py-0.5 rounded-full ${
                    engine.maintenance_status === "in-progress" ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" :
                    "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                  }`}>
                    {engine.maintenance_status === "in-progress" ? "Servicing" : "Queued"}
                  </span>
                ) : (
                  <Radio className={`w-5 h-5 ${
                    engine.status === "critical" ? "text-red-400" :
                    engine.status === "warning" ? "text-orange-400" : "text-green-400"
                  }`} />
                )}
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Health</span>
                  <span className={`font-bold ${
                    engine.status === "critical" ? "text-red-400" :
                    engine.status === "warning" ? "text-orange-400" : "text-green-400"
                  }`}>{engine.health}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">RUL</span>
                  <span className="text-cyan-400">{engine.rul}h</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Temp</span>
                  <span className="text-orange-400">{engine.temp}°C</span>
                </div>
                <div className="text-xs text-gray-500 mt-2">{engine.location}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {detailPanelEngineId && (detailLive || engineDetails) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white">Engine {detailTitleId} - Detailed Diagnostics</h3>
            <button type="button" onClick={closeEngineDetails} className="p-2 rounded-lg hover:bg-white/10">
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
          <div className="grid grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                  <div className="text-sm text-gray-400 mb-1">Health Status</div>
                  <div className="text-3xl font-bold text-cyan-400">{detailHealth ?? 'N/A'}%</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                  <div className="text-sm text-gray-400 mb-1">RUL</div>
                  <div className="text-2xl font-bold text-orange-400">{detailRul ?? 'N/A'}h</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                  <div className="text-sm text-gray-400 mb-1">Temp</div>
                  <div className="text-2xl font-bold text-red-400">{detailTemp ?? 'N/A'}°C</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                  <div className="text-sm text-gray-400 mb-1">Pressure</div>
                  <div className="text-2xl font-bold text-blue-400">{detailPressure != null ? detailPressure : 'N/A'}</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                  <div className="text-sm text-gray-400 mb-1">Vibration</div>
                  <div className="text-2xl font-bold text-purple-400">{detailVibration != null ? detailVibration : 'N/A'}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => scheduleMaintenance(
                  detailTitleId,
                  'Routine inspection',
                  new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                  'medium'
                )}
                disabled={loadingStates["schedule-maintenance"]}
                className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingStates["schedule-maintenance"] ? "Scheduling..." : "Schedule Maintenance"}
              </button>
            </div>
            <div className="col-span-2">
              <div className="h-full p-4 rounded-xl bg-white/5 border border-cyan-500/20">
                <h4 className="text-sm font-bold text-white mb-4">Sensor Readings (Last Hour)</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={engineTelemetryData}>
                    <XAxis dataKey="time" stroke="#666" />
                    <YAxis stroke="#666" />
                    <Tooltip labelFormatter={(v) => `Time: ${v}`} />
                    <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={2} />
                    <Line type="monotone" dataKey="pressure" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="vibration" stroke="#a855f7" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
    );
  };

  const renderInsightsView = () => (
    <div className="grid grid-cols-2 gap-6">
      <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">AI Predictions & Insights</h3>
        <div className="space-y-3">
          {dynamicInsights.map((insight, index) => (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-xl bg-white/5 border border-cyan-500/20 hover:bg-white/10 transition-all cursor-pointer"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center flex-shrink-0">
                  <Zap className="w-5 h-5 text-cyan-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-white mb-1">{insight.text}</p>
                  <span className="text-xs text-gray-500">{insight.time}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Model Performance</h3>
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Prediction Accuracy</span>
              <span className="text-lg font-bold text-green-400">{apiData.analytics?.metrics.accuracy ?? "94.7"}%</span>
            </div>
            <div className="h-3 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-green-500 to-cyan-500"
                initial={{ width: 0 }}
                animate={{ width: `${apiData.analytics?.metrics.accuracy ?? 94.7}%` }}
                transition={{ duration: 1.5 }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">False Positive Rate</span>
              <span className="text-lg font-bold text-orange-400">{apiData.analytics?.metrics.false_positive ?? "2.3"}%</span>
            </div>
            <div className="h-3 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-orange-500 to-red-500"
                initial={{ width: 0 }}
                animate={{ width: `${apiData.analytics?.metrics.false_positive ?? 2.3}%` }}
                transition={{ duration: 1.5 }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Detection Rate</span>
              <span className="text-lg font-bold text-cyan-400">{apiData.analytics?.metrics.detection_rate ?? "98.1"}%</span>
            </div>
            <div className="h-3 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                initial={{ width: 0 }}
                animate={{ width: `${apiData.analytics?.metrics.detection_rate ?? 98.1}%` }}
                transition={{ duration: 1.5 }}
              />
            </div>
          </div>

          <div className="mt-6 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
            <div className="text-xs text-gray-400 mb-2">Model Version</div>
            <div className="text-lg font-bold text-white">v3.7.2 - Production</div>
            <div className="text-xs text-cyan-400 mt-2">Last trained: 2 days ago</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAlertsView = () => (
    <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">Active Alerts & Notifications</h3>
        <div className="flex items-center gap-3">
          <button 
            onClick={markAllAlertsRead}
            disabled={loadingStates['mark-all-read']}
            className="px-4 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingStates['mark-all-read'] ? 'Marking All Read...' : 'Mark All Read'}
          </button>
          
          <div className="relative">
            <button 
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-cyan-500/10 text-gray-400 text-sm font-medium hover:bg-white/10"
            >
              <span>Filter: {alertSeverityFilter.charAt(0).toUpperCase() + alertSeverityFilter.slice(1)}</span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>
            
            <AnimatePresence>
              {showFilterPanel && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute right-0 mt-2 w-48 backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden z-50"
                >
                  {(['all', 'critical', 'warning', 'unacknowledged'] as const).map((filterOpt) => (
                    <button
                      key={filterOpt}
                      onClick={() => { setAlertSeverityFilter(filterOpt); setShowFilterPanel(false); }}
                      className={`w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/10 text-left text-sm text-white transition-all ${alertSeverityFilter === filterOpt ? "bg-cyan-500/10 text-cyan-400" : ""}`}
                    >
                      <span>{filterOpt.charAt(0).toUpperCase() + filterOpt.slice(1)}</span>
                      {alertSeverityFilter === filterOpt && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {alerts.filter(alert => {
          if (alertSeverityFilter === 'critical') return alert.severity === 'critical';
          if (alertSeverityFilter === 'warning') return alert.severity === 'warning';
          if (alertSeverityFilter === 'unacknowledged') return !alert.acknowledged;
          return true;
        }).map((alert) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`p-4 rounded-xl border-2 ${
              alert.severity === "critical" ? "bg-red-500/10 border-red-500/50" :
              alert.severity === "warning" ? "bg-orange-500/10 border-orange-500/50" :
              "bg-blue-500/10 border-blue-500/50"
            } ${alert.acknowledged ? "opacity-50" : ""}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                {alert.severity === "critical" ? (
                  <AlertOctagon className="w-5 h-5 text-red-400 mt-1" />
                ) : alert.severity === "warning" ? (
                  <AlertTriangle className="w-5 h-5 text-orange-400 mt-1" />
                ) : (
                  <CircleDot className="w-5 h-5 text-blue-400 mt-1" />
                )}
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-white">{alert.engine}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      alert.severity === "critical" ? "bg-red-500/20 text-red-400" :
                      alert.severity === "warning" ? "bg-orange-500/20 text-orange-400" :
                      "bg-blue-500/20 text-blue-400"
                    }`}>
                      {alert.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{alert.message}</p>
                  <span className="text-xs text-gray-500">{alert.time}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {!alert.acknowledged && (
                  <button 
                    onClick={() => acknowledgeAlert(alert.id)}
                    disabled={loadingStates[`ack-alert-${alert.id}`]}
                    className="px-3 py-1 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadingStates[`ack-alert-${alert.id}`] ? 'Acknowledging...' : 'Acknowledge'}
                  </button>
                )}
                <button 
                  onClick={() => clearAlert(alert.id)}
                  disabled={loadingStates[`clear-alert-${alert.id}`]}
                  className="p-1 rounded-lg hover:bg-white/10 disabled:opacity-50"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  const renderMaintenanceView = () => {
    const totalSavings = maintenanceHistory
      .filter(t => t.status === 'completed')
      .reduce((acc, t) => acc + (t.cost_saved || 0), 0);

    return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-6">
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-orange-500/20 border border-orange-500/50 flex items-center justify-center">
              <Wrench className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{maintenanceHistory.filter(t => t.status === 'scheduled').length}</div>
              <div className="text-xs text-gray-400">Scheduled</div>
              {maintenanceHistory.filter(t => t.status === 'suggested').length > 0 && (
                <div className="text-xs text-amber-400/90 mt-1">
                  {maintenanceHistory.filter(t => t.status === 'suggested').length} suggested (needs confirmation)
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center">
              <Activity className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{maintenanceHistory.filter(t => t.status === 'in-progress').length}</div>
              <div className="text-xs text-gray-400">In Progress</div>
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-green-500/20 border border-green-500/50 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{maintenanceHistory.filter(t => t.status === 'completed').length}</div>
              <div className="text-xs text-gray-400">Completed</div>
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-400">${totalSavings.toLocaleString()}</div>
              <div className="text-xs text-gray-400">Total Costs Saved</div>
            </div>
          </div>
        </div>
      </div>

      <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Maintenance Schedule</h3>
          <button onClick={() => setShowCreateMaintenanceModal(true)} className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium">
            + Schedule New
          </button>
        </div>

        <div className="space-y-3">
          {maintenanceHistory.map((task) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 rounded-xl bg-white/5 border border-cyan-500/20 hover:bg-white/10 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    task.status === "completed" ? "bg-green-500" :
                    task.status === "in-progress" ? "bg-cyan-500" :
                    task.status === "suggested" ? "bg-amber-400" :
                    "bg-orange-500"
                  }`} />
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-sm font-bold text-white">{task.engine}</span>
                      <span className="text-xs text-gray-500">•</span>
                      <span className="text-sm text-gray-300">{task.task}</span>
                      {task.status === "suggested" && (
                        <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          Suggested
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>{task.date}</span>
                      <span className={`px-2 py-0.5 rounded-full ${
                        task.priority === "high" ? "bg-red-500/20 text-red-400" :
                        task.priority === "medium" ? "bg-orange-500/20 text-orange-400" :
                        "bg-blue-500/20 text-blue-400"
                      }`}>
                        {task.priority}
                      </span>
                      {task.status === "in-progress" && (
                        <span className="text-cyan-400 font-medium animate-pulse flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                          Servicing...
                        </span>
                      )}
                    </div>
                    {task.status === "in-progress" && (
                      <div className="mt-2 w-48 sm:w-64">
                        <div className="flex justify-between text-[10px] text-cyan-400 mb-1">
                          <span>Progress Ticks</span>
                          <span>{Math.round(((task.progress_ticks || 0) / 10) * 100)}%</span>
                        </div>
                        <div className="h-1.5 bg-cyan-950 rounded-full overflow-hidden border border-cyan-500/20">
                          <motion.div 
                            className="h-full bg-cyan-400"
                            style={{ width: `${((task.progress_ticks || 0) / 10) * 100}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  {task.status === "suggested" && (
                    <>
                      <button
                        type="button"
                        onClick={() => maintenancePlannerAction(task.id, "confirm")}
                        disabled={!!loadingStates[`maint-action-${task.id}`]}
                        className="px-3 py-1 rounded-lg bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 text-xs font-medium disabled:opacity-50"
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        onClick={() => maintenancePlannerAction(task.id, "dismiss")}
                        disabled={!!loadingStates[`maint-action-${task.id}`]}
                        className="px-3 py-1 rounded-lg bg-white/5 border border-white/15 text-gray-400 text-xs font-medium hover:bg-white/10 disabled:opacity-50"
                      >
                        Dismiss
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setSelectedMaintenanceTask(
                      selectedMaintenanceTask?.id === task.id ? null : task
                    )}
                    className={`px-3 py-1 rounded-lg border text-xs font-medium transition-all ${
                      selectedMaintenanceTask?.id === task.id
                        ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'
                    }`}
                  >
                    {selectedMaintenanceTask?.id === task.id ? 'Hide Details' : 'View Details'}
                  </button>
                </div>
              </div>

              {/* Inline Detail Panel */}
              {selectedMaintenanceTask?.id === task.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-white/10"
                >
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Engine</div>
                      <div className="text-sm font-bold text-white">{task.engine}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Task</div>
                      <div className="text-sm font-bold text-white">{task.task}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Date</div>
                      <div className="text-sm font-bold text-white">{task.date}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Priority</div>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        task.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                        task.priority === 'medium' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {task.priority}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-2">
                    <div className="flex items-center gap-2">
                      <div className="text-xs text-gray-500">Status:</div>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        task.status === 'in-progress' ? 'bg-cyan-500/20 text-cyan-400' :
                        task.status === 'suggested' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-orange-500/20 text-orange-400'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    {task.status === "suggested" && (
                      <p className="text-xs text-gray-500 sm:ml-2">
                        Auto-drafted after sustained critical risk. Accept to schedule or dismiss if not needed.
                      </p>
                    )}
                  </div>

                  {task.status === "completed" && task.pre_service && task.post_service && (
                    <div className="mt-4 p-4 rounded-xl bg-white/5 border border-green-500/20">
                      <div className="text-xs font-bold text-green-400 mb-3 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        AI Maintenance Recovery Report
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider font-semibold">Pre-Service Status (Critical Risk)</div>
                          <div className="space-y-1.5 text-xs text-gray-300">
                            <div className="flex justify-between p-1 bg-red-500/5 rounded">
                              <span>Health Index:</span>
                              <span className="text-red-400 font-bold">{task.pre_service.health}%</span>
                            </div>
                            <div className="flex justify-between p-1 bg-red-500/5 rounded">
                              <span>Temperature:</span>
                              <span className="text-red-400 font-bold">{task.pre_service.temp}°C</span>
                            </div>
                            <div className="flex justify-between p-1 bg-red-500/5 rounded">
                              <span>Pressure:</span>
                              <span className="text-red-400 font-bold">{task.pre_service.pressure} psi</span>
                            </div>
                            <div className="flex justify-between p-1 bg-red-500/5 rounded">
                              <span>Vibration:</span>
                              <span className="text-red-400 font-bold">{task.pre_service.vibration} mm/s</span>
                            </div>
                            <div className="flex justify-between p-1 bg-red-500/5 rounded">
                              <span>RUL Estimate:</span>
                              <span className="text-red-400 font-bold">{task.pre_service.rul}h</span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider font-semibold">Post-Service Status (Restored)</div>
                          <div className="space-y-1.5 text-xs text-gray-300">
                            <div className="flex justify-between p-1 bg-emerald-500/5 rounded">
                              <span>Health Index:</span>
                              <span className="text-emerald-400 font-bold">{task.post_service.health}%</span>
                            </div>
                            <div className="flex justify-between p-1 bg-emerald-500/5 rounded">
                              <span>Temperature:</span>
                              <span className="text-emerald-400 font-bold">{task.post_service.temp}°C</span>
                            </div>
                            <div className="flex justify-between p-1 bg-emerald-500/5 rounded">
                              <span>Pressure:</span>
                              <span className="text-emerald-400 font-bold">{task.post_service.pressure} psi</span>
                            </div>
                            <div className="flex justify-between p-1 bg-emerald-500/5 rounded">
                              <span>Vibration:</span>
                              <span className="text-emerald-400 font-bold">{task.post_service.vibration} mm/s</span>
                            </div>
                            <div className="flex justify-between p-1 bg-emerald-500/5 rounded">
                              <span>RUL Estimate:</span>
                              <span className="text-emerald-400 font-bold">{task.post_service.rul}h</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 text-[10px] text-emerald-400 font-semibold text-right">
                        Financial Impact: ${task.cost_saved?.toLocaleString()} Saved in Downtime Prevention
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

  const renderAnalyticsView = () => {
    const fleetData = displayedFleet;
    const activeLeadUnit = analyticsData[0]?.lead_time_unit || "days";
    
    return (
    <div className="space-y-6">
      {/* Real-World Industry Insight Panel */}
      <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-200 text-xs">
        <span className="font-bold">Prognostic Metrics Insight:</span> Real-world Predictive Maintenance (PdM) systems evaluate model reliability using <span className="text-cyan-400 font-semibold">Proactive Lead Time</span> (Prognosis Horizon)—the warning runway available to order parts and schedule crews—alongside standard ML metrics like <span className="text-cyan-400 font-semibold">False Alarm Rate</span> (to prevent alarm fatigue) and <span className="text-cyan-400 font-semibold">Recall / Failure Detection Rate</span>.
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Failure Prediction Performance - Dual-Axis Composed Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white">Failure Prediction Performance</h3>
            <span className="text-xs text-gray-400">Lead Time Unit: <span className="text-amber-400 font-semibold uppercase">{activeLeadUnit}</span></span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={analyticsData} margin={{ top: 10, right: 5, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 10 }} />
              <YAxis yAxisId="left" stroke="#9ca3af" tick={{ fontSize: 10 }} label={{ value: 'Events Count', angle: -90, position: 'insideLeft', fill: '#9ca3af', style: { fontSize: 10 } }} />
              <YAxis yAxisId="right" orientation="right" stroke="#fbbf24" tick={{ fontSize: 10 }} label={{ value: `Lead Time (${activeLeadUnit})`, angle: 90, position: 'insideRight', fill: '#fbbf24', style: { fontSize: 10 } }} />
              <Tooltip 
                contentStyle={{ backgroundColor: "#0d1117", border: "1px solid rgba(6, 182, 212, 0.3)", borderRadius: "8px" }}
                labelStyle={{ color: "#fff", fontWeight: "bold", fontSize: 11 }}
                itemStyle={{ fontSize: 11 }}
              />
              <Legend wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
              <Bar yAxisId="left" dataKey="predictions" name="Predicted Failures (AI)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="left" dataKey="failures" name="Actual Failures" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="lead_time" name="Avg Proactive Lead Time" stroke="#fbbf24" strokeWidth={3} dot={{ fill: '#fbbf24', r: 4 }} activeDot={{ r: 6 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Fleet Status Distribution Pie Chart */}
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Fleet Status Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <RPieChart>
              <Pie
                data={[
                  { name: 'Critical', value: apiData.analytics?.distribution.critical ?? fleetData.filter(e => e.status === 'critical').length },
                  { name: 'Warning', value: apiData.analytics?.distribution.warning ?? fleetData.filter(e => e.status === 'warning').length },
                  { name: 'Healthy', value: apiData.analytics?.distribution.healthy ?? fleetData.filter(e => e.status === 'healthy').length },
                ]}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {[0, 1, 2].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: "#0d1117", border: "1px solid rgba(6, 182, 212, 0.3)", borderRadius: "8px", fontSize: 11 }}
              />
            </RPieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Industrial-Grade Performance metrics */}
      <div className="grid grid-cols-3 gap-6">
        {/* Model Accuracy Card */}
        <div className="backdrop-blur-xl bg-white/5 border border-cyan-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {apiData.analytics?.metrics.accuracy ?? 96.4}%
              </div>
              <div className="text-xs text-gray-400">Model F1 Accuracy</div>
            </div>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Fleet-wide test set prediction balance (precision & recall ratio). Nominal baseline target &gt; 94%.
          </p>
        </div>

        {/* False Positive / False Alarm Rate Card */}
        <div className="backdrop-blur-xl bg-white/5 border border-red-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-red-500/20 border border-red-500/50 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {apiData.analytics?.metrics.false_positive ?? 2.8}%
              </div>
              <div className="text-xs text-gray-400">False Alarm Rate</div>
            </div>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Unnecessary proactive inspection trigger percentage. Lower FAR prevents engineering team alert fatigue.
          </p>
        </div>

        {/* Recall / Failure Detection Rate Card */}
        <div className="backdrop-blur-xl bg-white/5 border border-green-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-green-500/20 border border-green-500/50 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {apiData.analytics?.metrics.detection_rate ?? 98.7}%
              </div>
              <div className="text-xs text-gray-400">Failure Detection Rate</div>
            </div>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Percentage of actual critical failure events correctly anticipated in advance. Goal: absolute coverage.
          </p>
        </div>
      </div>
    </div>
    );
  };


  const renderContent = () => {
    switch (activeNav) {
      case "dashboard": return renderDashboardView();
      case "engines": return renderEnginesView();
      case "insights": return renderInsightsView();
      case "alerts": return renderAlertsView();
      case "maintenance": return renderMaintenanceView();
      case "analytics": return renderAnalyticsView();
      default: return renderDashboardView();
    }
  };

  return (
    <div className="relative size-full overflow-hidden bg-[#0a0e1a]">
      {/* Left Sidebar */}
      <div className="fixed left-0 top-0 h-full w-16 bg-[#0d1117] border-r border-cyan-500/20 flex flex-col items-center py-6 z-50">
        <motion.div
          className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-8"
          animate={{ boxShadow: ["0 0 20px rgba(6, 182, 212, 0.3)", "0 0 30px rgba(6, 182, 212, 0.5)", "0 0 20px rgba(6, 182, 212, 0.3)"] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Shield className="w-6 h-6 text-white" />
        </motion.div>

        <div className="flex-1 flex flex-col gap-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.id} className="relative group">
                <motion.button
                  onClick={() => setActiveNav(item.id)}
                  className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
                    activeNav === item.id ? "bg-cyan-500/20 border border-cyan-500/50" : "bg-white/5 border border-white/10 hover:bg-white/10"
                  }`}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Icon className={`w-5 h-5 ${activeNav === item.id ? "text-cyan-400" : "text-gray-400"}`} />
                </motion.button>

                {/* Tooltip */}
                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#0d1117] border border-cyan-500/30 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  <span className="text-xs text-white font-medium">{item.label}</span>
                </div>
              </div>
            );
          })}
        </div>

        <motion.div
          onClick={() => setShowAlertPanel(!showAlertPanel)}
          className="w-10 h-10 rounded-lg bg-red-500/20 border border-red-500/50 flex items-center justify-center relative cursor-pointer"
          animate={{ boxShadow: ["0 0 10px rgba(239, 68, 68, 0.3)", "0 0 20px rgba(239, 68, 68, 0.6)", "0 0 10px rgba(239, 68, 68, 0.3)"] }}
          transition={{ duration: 2, repeat: Infinity }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell className="w-5 h-5 text-red-400" />
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
            <span className="text-white text-xs font-bold">{alerts.filter(a => !a.acknowledged).length}</span>
          </div>
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="ml-16 h-full flex flex-col">
        {/* Top Bar */}
        <div className="h-16 bg-[#0d1117] border-b border-cyan-500/20 px-6 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-bold text-white tracking-wider">NEXUS AI COMMAND CENTER</h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/30">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <span className="text-xs text-green-400 font-medium">Operational</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                <Wifi className="w-3 h-3 text-cyan-400" />
                <span className="text-xs text-cyan-400 font-medium">Streaming</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-xs text-gray-400 font-mono">{currentTime.toLocaleTimeString()}</div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30">
              <motion.div className="w-2 h-2 rounded-full bg-red-400" animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.5, repeat: Infinity }} />
              <span className="text-xs text-red-400 font-medium">{apiData.fleet?.critical_count || 0} LIVE</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/30">
              <AlertTriangle className="w-3 h-3 text-orange-400" />
              <span className="text-xs text-orange-400 font-medium">{alerts.filter(a => !a.acknowledged).length} Alerts</span>
            </div>
            {/* User Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
              >
                <User className="w-3 h-3 text-cyan-400" />
                <span className="text-xs text-white font-medium">{currentUser?.operatorId || "Operator"}</span>
                <ChevronDown className="w-3 h-3 text-gray-400" />
              </button>

              <AnimatePresence>
                {showUserMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute top-full right-0 mt-2 w-56 backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden z-50"
                  >
                    {/* User Info */}
                    <div className="p-4 border-b border-white/10">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                          <User className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white">{currentUser?.operatorId}</p>
                          <p className="text-xs text-gray-400">{currentUser?.role}</p>
                        </div>
                      </div>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">

                    </div>

                    <div className="border-t border-white/10 p-2">
                      <button
                        onClick={handleLogout}
                        className="w-full px-4 py-2.5 text-left text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-all flex items-center gap-3"
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Control Bar */}
        <div className="h-14 bg-[#0d1117]/50 border-b border-cyan-500/10 px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Machine Type Selector */}
            <div className="relative">
              <button
                onClick={() => setShowMachineDropdown(!showMachineDropdown)}
                className="flex items-center gap-3 px-4 py-2 rounded-lg bg-white/5 border border-cyan-500/30 hover:bg-white/10 transition-all"
              >
                <span className="text-2xl">{selectedMachine.icon}</span>
                <div className="text-left">
                  <div className="text-xs text-gray-400">Machine Type</div>
                  <div className="text-sm text-white font-medium">{selectedMachine.name}</div>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>

              <AnimatePresence>
                {showMachineDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute top-full mt-2 left-0 w-64 backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden z-50"
                  >
                    {machineTypes.map((machine) => (
                      <button
                        key={machine.id}
                        onClick={() => { setSelectedMachine(machine); setShowMachineDropdown(false); }}
                        className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 transition-all ${selectedMachine.id === machine.id ? "bg-cyan-500/10" : ""}`}
                      >
                        <span className="text-2xl">{machine.icon}</span>
                        <div className="flex-1 text-left">
                          <div className="text-sm text-white font-medium">{machine.name}</div>
                          <div className="text-xs text-gray-400">{machine.count} units</div>
                        </div>
                        {selectedMachine.id === machine.id && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Time Range Selector */}
            <div className="relative">
              <button
                onClick={() => setShowTimeDropdown(!showTimeDropdown)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-cyan-500/30 hover:bg-white/10 transition-all"
              >
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-sm text-white font-medium">{selectedTimeRange.label}</span>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>

              <AnimatePresence>
                {showTimeDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute top-full mt-2 left-0 w-48 backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden z-50"
                  >
                    {timeRanges.map((range) => (
                      <button
                        key={range.id}
                        onClick={() => { setSelectedTimeRange(range); setShowTimeDropdown(false); }}
                        className={`w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/10 transition-all ${selectedTimeRange.id === range.id ? "bg-cyan-500/10" : ""}`}
                      >
                        <span className="text-sm text-white">{range.label}</span>
                        {selectedTimeRange.id === range.id && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <motion.button 
              type="button" 
              whileHover={{ scale: 1.05 }} 
              whileTap={{ scale: 0.95 }} 
              onClick={handleManualRefresh} 
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-cyan-500/30 hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 text-cyan-400 ${isRefreshing ? "animate-spin" : ""}`} />
              <span className="text-sm text-white font-medium">
                {isRefreshing ? "Refreshing..." : "Refresh"}
              </span>
            </motion.button>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search engines..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 w-64 bg-white/5 border border-cyan-500/30 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50" 
              />
            </div>

            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => setShowReportModal(true)} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium shadow-lg shadow-cyan-500/30">
              <FileText className="w-4 h-4" />
              <span className="text-sm">Generate Report</span>
            </motion.button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeNav}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Alert Sidebar Panel */}
      <AnimatePresence>
        {showAlertPanel && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90]"
              onClick={() => setShowAlertPanel(false)}
            />

            {/* Sliding Panel */}
            <motion.div
              initial={{ x: -400 }}
              animate={{ x: 0 }}
              exit={{ x: -400 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-16 top-0 bottom-0 w-96 backdrop-blur-xl bg-[#0d1117] border-r border-cyan-500/30 shadow-2xl z-[100] overflow-hidden flex flex-col"
            >
              {/* Panel Header */}
              <div className="p-6 border-b border-cyan-500/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-red-500/20 border border-red-500/50 flex items-center justify-center">
                      <Bell className="w-5 h-5 text-red-400" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">Active Alerts</h2>
                      <p className="text-xs text-gray-400">{alerts.filter(a => !a.acknowledged).length} unacknowledged</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowAlertPanel(false)}
                    className="p-2 rounded-lg hover:bg-white/10 transition-all"
                  >
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-2">
                  <button 
                    onClick={markAllAlertsRead}
                    disabled={loadingStates['mark-all-read']}
                    className="flex-1 px-3 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 text-xs font-medium hover:bg-cyan-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadingStates['mark-all-read'] ? 'Marking All Read...' : 'Mark All Read'}
                  </button>
                  <button 
                    onClick={clearAllAlerts}
                    disabled={loadingStates['clear-all']}
                    className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 text-xs font-medium hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadingStates['clear-all'] ? 'Clearing...' : 'Clear All'}
                  </button>
                </div>
              </div>

              {/* Alerts List */}
              <div className="flex-1 overflow-auto p-4 space-y-3">
                {alerts.map((alert, index) => (
                  <motion.div
                    key={alert.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`p-4 rounded-xl border-2 ${
                      alert.severity === "critical"
                        ? "bg-red-500/10 border-red-500/50"
                        : alert.severity === "warning"
                        ? "bg-orange-500/10 border-orange-500/50"
                        : "bg-blue-500/10 border-blue-500/50"
                    } ${alert.acknowledged ? "opacity-50" : ""}`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        {alert.severity === "critical" ? (
                          <motion.div
                            animate={{
                              scale: [1, 1.2, 1],
                            }}
                            transition={{ duration: 1, repeat: Infinity }}
                          >
                            <AlertOctagon className="w-5 h-5 text-red-400 flex-shrink-0" />
                          </motion.div>
                        ) : alert.severity === "warning" ? (
                          <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        ) : (
                          <CircleDot className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-bold text-white">{alert.engine}</span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                alert.severity === "critical"
                                  ? "bg-red-500/20 text-red-400"
                                  : alert.severity === "warning"
                                  ? "bg-orange-500/20 text-orange-400"
                                  : "bg-blue-500/20 text-blue-400"
                              }`}
                            >
                              {alert.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-300 mb-2">{alert.message}</p>
                          <div className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-gray-500" />
                            <span className="text-xs text-gray-500">{alert.time}</span>
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => clearAlert(alert.id)}
                        disabled={loadingStates[`clear-alert-${alert.id}`]}
                        className="p-1 rounded-lg hover:bg-white/10 disabled:opacity-50 flex-shrink-0"
                        aria-label="Clear alert"
                      >
                        <X className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>

                    {/* Alert Actions */}
                    <div className="flex items-center gap-2 pt-3 border-t border-white/10">
                      {!alert.acknowledged ? (
                        <>
                          <button 
                            onClick={() => acknowledgeAlert(alert.id)}
                            disabled={loadingStates[`ack-alert-${alert.id}`]}
                            className="flex-1 px-3 py-1.5 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 text-xs font-medium hover:bg-cyan-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {loadingStates[`ack-alert-${alert.id}`] ? 'Acknowledging...' : 'Acknowledge'}
                          </button>
                          <button className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 text-xs font-medium hover:bg-white/10 transition-all">
                            View Details
                          </button>
                        </>
                      ) : (
                        <div className="flex items-center gap-2 text-xs text-green-400">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Acknowledged</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Panel Footer */}
              <div className="p-4 border-t border-cyan-500/20">
                <button
                  onClick={() => {
                    setShowAlertPanel(false);
                    setActiveNav("alerts");
                  }}
                  className="w-full px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium hover:shadow-lg hover:shadow-cyan-500/30 transition-all"
                >
                  View All Alerts
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Report Generation Modal */}
      <AnimatePresence>
        {showReportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100]"
            onClick={() => !isGeneratingReport && setShowReportModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-lg backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-2xl p-8 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Generate Report</h2>
                {!isGeneratingReport && (
                  <button onClick={() => setShowReportModal(false)} className="p-2 rounded-lg hover:bg-white/10 transition-all">
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                )}
              </div>

              {!isGeneratingReport ? (
                <>
                  <div className="space-y-4 mb-6">
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Report Type</label>
                      <select className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:border-cyan-500/50">
                        <option>Predictive Maintenance Summary</option>
                        <option>Detailed Fleet Analysis</option>
                        <option>Critical Alerts Report</option>
                        <option>Performance Metrics</option>
                        <option>Custom Report</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Time Period</label>
                      <select className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:border-cyan-500/50">
                        <option>Last 24 Hours</option>
                        <option>Last 7 Days</option>
                        <option>Last 30 Days</option>
                        <option>Custom Range</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Format</label>
                      <div className="grid grid-cols-3 gap-3">
                        <button 
                          onClick={() => setSelectedReportFormat('pdf')}
                          className={`px-4 py-3 rounded-lg font-medium transition-all ${
                            selectedReportFormat === 'pdf' 
                              ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400' 
                              : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                          }`}
                        >
                          PDF
                        </button>
                        <button 
                          onClick={() => setSelectedReportFormat('excel')}
                          className={`px-4 py-3 rounded-lg font-medium transition-all ${
                            selectedReportFormat === 'excel' 
                              ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400' 
                              : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                          }`}
                        >
                          Excel
                        </button>
                        <button 
                          onClick={() => setSelectedReportFormat('csv')}
                          className={`px-4 py-3 rounded-lg font-medium transition-all ${
                            selectedReportFormat === 'csv' 
                              ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400' 
                              : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                          }`}
                        >
                          CSV
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Include</label>
                      <div className="space-y-2">
                        {["Charts & Visualizations", "AI Predictions", "Raw Data", "Recommendations"].map((item) => (
                          <label key={item} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10">
                            <input type="checkbox" defaultChecked className="w-4 h-4 text-cyan-500" />
                            <span className="text-sm text-gray-300">{item}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>

                  <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={handleGenerateReport} className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium rounded-lg shadow-lg shadow-cyan-500/30 flex items-center justify-center gap-2">
                    <Download className="w-5 h-5" />
                    Generate Report
                  </motion.button>
                </>
              ) : (
                <div className="py-12 flex flex-col items-center">
                  <motion.div className="w-16 h-16 rounded-full border-4 border-cyan-500/30 border-t-cyan-500" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} />
                  <p className="text-white mt-6 text-lg">Generating report...</p>
                  <p className="text-gray-400 text-sm mt-2">Processing data and creating visualizations</p>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Maintenance Modal */}
      <AnimatePresence>
        {showCreateMaintenanceModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100]"
            onClick={() => setShowCreateMaintenanceModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-lg backdrop-blur-xl bg-[#0d1117] border border-cyan-500/30 rounded-2xl p-8 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Schedule Maintenance</h2>
                <button onClick={() => setShowCreateMaintenanceModal(false)} className="p-2 rounded-lg hover:bg-white/10 transition-all">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Engine ID</label>
                  <input
                    type="text"
                    placeholder="e.g. E-001"
                    value={newMaintenanceEngine}
                    onChange={(e) => setNewMaintenanceEngine(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Task</label>
                  <input
                    type="text"
                    placeholder="e.g. Oil change"
                    value={newMaintenanceTask}
                    onChange={(e) => setNewMaintenanceTask(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Date</label>
                  <input
                    type="date"
                    value={newMaintenanceDate}
                    onChange={(e) => setNewMaintenanceDate(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Priority</label>
                  <select
                    value={newMaintenancePriority}
                    onChange={(e) => setNewMaintenancePriority(e.target.value as 'high' | 'medium' | 'low')}
                    className="w-full px-4 py-3 bg-white/5 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleCreateMaintenance}
                disabled={loadingStates["schedule-maintenance"]}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium rounded-lg shadow-lg shadow-cyan-500/30 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Wrench className="w-5 h-5" />
                {loadingStates["schedule-maintenance"] ? "Scheduling..." : "Schedule Maintenance"}
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Notification System */}
      <div className="fixed top-20 right-6 z-50 space-y-2">
        <AnimatePresence>
          {notifications.map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }}
              className={`p-4 rounded-lg border-2 shadow-lg ${
                notification.type === 'success' 
                  ? 'bg-green-500/10 border-green-500/50' 
                  : 'bg-red-500/10 border-red-500/50'
              }`}
            >
              <div className="flex items-center gap-3">
                {notification.type === 'success' ? (
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
                <span className={`text-sm font-medium ${
                  notification.type === 'success' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {notification.message}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Session Timeout Warning Modal */}
      <AnimatePresence>
        {showSessionWarning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[110]"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-md backdrop-blur-xl bg-[#0d1117] border-2 border-orange-500/50 rounded-2xl p-8 shadow-2xl"
            >
              <div className="text-center">
                <motion.div
                  className="w-16 h-16 mx-auto mb-4 rounded-full bg-orange-500/20 border-2 border-orange-500/50 flex items-center justify-center"
                  animate={{
                    boxShadow: ["0 0 20px rgba(249, 115, 22, 0.3)", "0 0 40px rgba(249, 115, 22, 0.6)", "0 0 20px rgba(249, 115, 22, 0.3)"],
                  }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <Timer className="w-8 h-8 text-orange-400" />
                </motion.div>

                <h2 className="text-2xl font-bold text-white mb-2">Session Expiring Soon</h2>
                <p className="text-gray-400 text-sm mb-6">
                  Your session will expire in{" "}
                  <span className="text-orange-400 font-bold">
                    {formatTimeRemaining(sessionTimeRemaining)}
                  </span>
                </p>

                <div className="flex gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleExtendSession}
                    className="flex-1 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium rounded-lg shadow-lg shadow-cyan-500/30"
                  >
                    Extend Session
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleLogout}
                    className="flex-1 py-3 bg-white/5 border border-white/10 text-gray-400 font-medium rounded-lg hover:bg-white/10"
                  >
                    Logout
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
