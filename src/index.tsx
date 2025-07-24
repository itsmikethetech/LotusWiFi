import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  TextField,
  staticClasses
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster
} from "@decky/api"
import { useState, useEffect } from "react";
import { FaWifi } from "react-icons/fa";

interface Settings {
  max_latency: number;
  check_interval: number;
  ping_host: string;
  enabled: boolean;
}

interface PingResult {
  latency: number;
  status: string;
  timestamp: number;
}

interface Status {
  is_monitoring: boolean;
  last_ping: PingResult;
  restart_count: number;
  settings: Settings;
}

const getSettings = callable<[], Settings>("get_settings");
const updateSettings = callable<[Settings], boolean>("update_settings");
const getStatus = callable<[], Status>("get_status");
const startMonitoring = callable<[], boolean>("start_monitoring");
const stopMonitoring = callable<[], boolean>("stop_monitoring");

function Content() {
  const [settings, setSettings] = useState<Settings>({
    max_latency: 100,
    check_interval: 10,
    ping_host: "8.8.8.8",
    enabled: false
  });
  const [status, setStatus] = useState<Status | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [currentSettings, currentStatus] = await Promise.all([
        getSettings(),
        getStatus()
      ]);
      setSettings(currentSettings);
      setStatus(currentStatus);
    } catch (error) {
      console.error("Failed to load initial data:", error);
      toaster.toast({
        title: "Error",
        body: "Failed to load plugin data"
      });
    }
  };

  const handleSettingsChange = async (newSettings: Partial<Settings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    
    try {
      setIsLoading(true);
      const success = await updateSettings(updatedSettings);
      if (success) {
        const newStatus = await getStatus();
        setStatus(newStatus);
      } else {
        toaster.toast({
          title: "Error",
          body: "Failed to update settings"
        });
      }
    } catch (error) {
      console.error("Settings update failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      setIsLoading(true);
      let success: boolean;
      
      if (status?.is_monitoring) {
        success = await stopMonitoring();
      } else {
        success = await startMonitoring();
      }
      
      if (success) {
        const newStatus = await getStatus();
        setStatus(newStatus);
        toaster.toast({
          title: status?.is_monitoring ? "Stopped" : "Started",
          body: `LotusWiFi script ${status?.is_monitoring ? "stopped" : "started"}`
        });
      }
    } catch (error) {
      console.error("Failed to toggle monitoring:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatLatency = (latency: number): string => {
    if (latency < 0) return "Failed";
    return `${latency.toFixed(1)}ms`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "ok": return "#4ade80";
      case "high": return "#f59e0b";
      case "failed": return "#ef4444";
      default: return "#6b7280";
    }
  };

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <>
      <PanelSection title="LotusWiFi Script Status">
        <PanelSectionRow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Script Status:</span>
            <span style={{ color: status?.is_monitoring ? "#4ade80" : "#ef4444" }}>
              {status?.is_monitoring ? "Running" : "Stopped"}
            </span>
          </div>
        </PanelSectionRow>
        
        {status?.last_ping && (
          <>
            <PanelSectionRow>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Last Ping:</span>
                <span style={{ color: getStatusColor(status.last_ping.status) }}>
                  {formatLatency(status.last_ping.latency)}
                </span>
              </div>
            </PanelSectionRow>
            
            <PanelSectionRow>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Last Check:</span>
                <span style={{ fontSize: "0.9em", opacity: 0.8 }}>
                  {status.last_ping.timestamp > 0 ? formatTimestamp(status.last_ping.timestamp) : "Never"}
                </span>
              </div>
            </PanelSectionRow>
          </>
        )}
        
        <PanelSectionRow>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Wi-Fi Restarts:</span>
            <span>{status?.restart_count || 0}</span>
          </div>
        </PanelSectionRow>
        
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={toggleMonitoring}
            disabled={isLoading}
          >
            {status?.is_monitoring ? "Stop Script" : "Start Script"}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Settings">
        <PanelSectionRow>
          <SliderField
            label="Max Latency (ms)"
            value={settings.max_latency}
            min={50}
            max={500}
            step={10}
            onChange={(value) => handleSettingsChange({ max_latency: value })}
            disabled={isLoading}
          />
        </PanelSectionRow>
        
        <PanelSectionRow>
          <SliderField
            label="Check Interval (seconds)"
            value={settings.check_interval}
            min={5}
            max={60}
            step={5}
            onChange={(value) => handleSettingsChange({ check_interval: value })}
            disabled={isLoading}
          />
        </PanelSectionRow>
        
        <PanelSectionRow>
          <TextField
            label="Ping Host"
            value={settings.ping_host}
            onChange={(e) => handleSettingsChange({ ping_host: e.target.value })}
            disabled={isLoading}
          />
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}

export default definePlugin(() => {
  console.log("LotusWiFi plugin initializing")

  const pingResultListener = addEventListener<[PingResult]>("ping_result", (result) => {
    console.log("Ping result:", result);
  });

  const wifiStatusListener = addEventListener<[{ monitoring: boolean }]>("wifi_status_changed", (data) => {
    console.log("WiFi status changed:", data);
  });

  const wifiRestartListener = addEventListener<[{ count: number; reason: string }]>("wifi_restarted", (data) => {
    console.log("WiFi restarted:", data);
    toaster.toast({
      title: "Wi-Fi Restarted",
      body: `Restart #${data.count}: ${data.reason}`
    });
  });

  return {
    name: "LotusWiFi",
    titleView: <div className={staticClasses.Title}>LotusWiFi Monitor</div>,
    content: <Content />,
    icon: <FaWifi />,
    onDismount() {
      console.log("LotusWiFi plugin unloading")
      removeEventListener("ping_result", pingResultListener);
      removeEventListener("wifi_status_changed", wifiStatusListener);
      removeEventListener("wifi_restarted", wifiRestartListener);
    },
  };
});
