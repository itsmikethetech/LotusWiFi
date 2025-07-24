# LotusWiFi - DeckyLoader Plugin

A Steam Deck plugin that provides an easy-to-use interface for running the LotusWiFi monitoring script. This plugin gives you Steam Deck UI controls to start/stop your proven Wi-Fi monitoring script and configure its settings. Original script by **wanderingxlotus**.

## Features

- **Script Wrapper**: Runs your original, tested `wifitoggler` bash script
- **Steam Deck UI Integration**: Native controls to start/stop the script and adjust settings
- **Real-time Status**: Shows script output and Wi-Fi restart notifications
- **Configurable Settings**: Adjust latency threshold, check interval, and ping target through the UI
- **Persistent Settings**: Settings are automatically applied to the script and saved
- **Live Monitoring**: See ping results and restart counts in real-time

## Settings

- **Max Latency**: Maximum acceptable latency in milliseconds (50-500ms, default: 100ms)
- **Check Interval**: Time between ping checks in seconds (5-60s, default: 10s)
- **Ping Host**: Target host for latency testing (default: 8.8.8.8)

## How It Works

The plugin creates a modified version of your `wifitoggler` script with your chosen settings and runs it in the background. It monitors the script's output to provide real-time status updates in the Steam Deck UI.

## Usage

1. Install the plugin through DeckyLoader
2. Open the plugin from the DeckyLoader menu
3. Configure your preferred settings (latency threshold, check interval, ping host)
4. Click "Start Script" to begin Wi-Fi monitoring
5. The original `wifitoggler` script runs in the background and restarts Wi-Fi when needed
6. View real-time status and restart notifications in the plugin UI

## Status Indicators

- **Script Status**: Shows if the `wifitoggler` script is running or stopped
- **Last Ping**: Latest latency measurement with color coding:
  - Green: Normal latency (≤ threshold)
  - Orange: High latency (> threshold)  
  - Red: Ping failed
- **Last Check**: Timestamp of the most recent ping
- **Wi-Fi Restarts**: Total number of automatic Wi-Fi restarts performed by the script

## Requirements

- Steam Deck with DeckyLoader installed
- Root privileges (plugin uses `_root` flag)
- `ping` and `rfkill` utilities (pre-installed on Steam Deck)

## Installation

### Via DeckyLoader Plugin Store (Recommended)
*Coming soon - plugin needs to be submitted to the store*

### Manual Installation
1. Download the latest release
2. Extract to your DeckyLoader plugins directory
3. Restart DeckyLoader or reload plugins

## Development

### Prerequisites
- Node.js v16.14+
- pnpm v9
- Docker (for custom backends)

### Building
```bash
pnpm install
pnpm run build
```

### Development with hot reload
```bash
pnpm run dev
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter issues or have questions:
1. Check the DeckyLoader logs for error messages
2. Verify that `ping` and `rfkill` commands work on your system
3. Submit an issue on GitHub with detailed information
