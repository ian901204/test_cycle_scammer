import webview
import os
import json
from scan import collect_data_with_test_cycle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

# File to store last visited path
LAST_PATH_FILE = os.path.join(os.path.expanduser('~'), '.test_cycle_analyzer_last_path.json')

class API:
    def __init__(self):
        self.selected_folders = []
        self.boards_data = {}  # Store analyzed data for all boards -> channels
        self.channels_data = {}  # Store analyzed data for current board's channels
        self.last_browsed_path = None
        
    def get_initial_path(self):
        """Get the initial path to load"""
        try:
            if os.path.exists(LAST_PATH_FILE):
                with open(LAST_PATH_FILE, 'r') as f:
                    data = json.load(f)
                    last_path = data.get('last_path')
                    if last_path and os.path.exists(last_path):
                        # Return parent directory of last path
                        parent_path = os.path.dirname(last_path)
                        if os.path.exists(parent_path):
                            return parent_path
        except Exception as e:
            print(f"Error reading last path: {e}")
        return os.path.expanduser('~')
    
    def save_last_path(self, path):
        """Save the last browsed path"""
        try:
            with open(LAST_PATH_FILE, 'w') as f:
                json.dump({'last_path': path}, f)
        except Exception as e:
            print(f"Error saving last path: {e}")
        
    def list_folders(self, path=None):
        """List folders in a given directory"""
        if path is None:
            path = self.get_initial_path()
        
        # Save the current path
        if path and os.path.isdir(path):
            self.last_browsed_path = path
            self.save_last_path(path)
        
        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path) and not item.startswith('.'):
                    items.append({
                        'name': item,
                        'path': full_path,
                        'isDirectory': True
                    })
            items.sort(key=lambda x: x['name'].lower())
            return {
                'success': True,
                'currentPath': path,
                'parent': os.path.dirname(path) if path != '/' else None,
                'items': items
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def select_folder(self, path):
        """Add a folder to selection"""
        if path not in self.selected_folders:
            if len(self.selected_folders) < 5:
                self.selected_folders.append(path)
                return {'success': True, 'folders': self.selected_folders}
            else:
                return {'success': False, 'error': 'Maximum 5 folders allowed'}
        return {'success': True, 'folders': self.selected_folders}
    
    def remove_folder(self, index):
        """Remove a folder from selection"""
        try:
            if 0 <= index < len(self.selected_folders):
                self.selected_folders.pop(index)
            return {'success': True, 'folders': self.selected_folders}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def clear_folders(self):
        """Clear all selected folders"""
        self.selected_folders = []
        return {'success': True, 'folders': []}
    
    def _generate_all_channels_plot(self):
        """Generate plot with all channels"""
        test_cycles = [1, 2, 3, 4, 5]
        fig, axs = plt.subplots(3, 1, figsize=(10, 14))
        
        # Calculate statistics for outlier detection
        
        # Calculate mean for each channel across all test cycles
        channel_means = {'pf': {}, 'vf': {}, 'ith': {}}
        for ch in self.channels_data.keys():
            channel_means['pf'][ch] = np.mean(self.channels_data[ch]['pf'])
            channel_means['vf'][ch] = np.mean(self.channels_data[ch]['vf'])
            channel_means['ith'][ch] = np.mean(self.channels_data[ch]['ith'])
        
        # Calculate overall mean and std from channel means
        overall_mean_pf = np.mean(list(channel_means['pf'].values()))
        overall_std_pf = np.std(list(channel_means['pf'].values()))
        overall_mean_vf = np.mean(list(channel_means['vf'].values()))
        overall_std_vf = np.std(list(channel_means['vf'].values()))
        overall_mean_ith = np.mean(list(channel_means['ith'].values()))
        overall_std_ith = np.std(list(channel_means['ith'].values()))
        
        # Detect outliers (channels beyond 2 standard deviations)
        outlier_threshold = 2
        outliers_pf = {ch: mean for ch, mean in channel_means['pf'].items() 
                       if abs(mean - overall_mean_pf) > outlier_threshold * overall_std_pf}
        outliers_vf = {ch: mean for ch, mean in channel_means['vf'].items() 
                       if abs(mean - overall_mean_vf) > outlier_threshold * overall_std_vf}
        outliers_ith = {ch: mean for ch, mean in channel_means['ith'].items() 
                        if abs(mean - overall_mean_ith) > outlier_threshold * overall_std_ith}
        
        # Plot Pf
        axs[0].set_title(f'Pf over Test (Mean: {overall_mean_pf:.2f} ± {overall_std_pf:.2f})')
        axs[0].set_xlabel('Test Cycle')
        axs[0].set_ylabel('Pf')
        axs[0].set_xlim(0.5, 5.5)
        axs[0].grid(True, alpha=0.3)
        axs[0].axhline(y=overall_mean_pf, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[0].axhline(y=overall_mean_pf + 2*overall_std_pf, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[0].axhline(y=overall_mean_pf - 2*overall_std_pf, color='orange', linestyle=':', alpha=0.5)
        
        # Plot Vf
        axs[1].set_title(f'Vf over Test (Mean: {overall_mean_vf:.2f} ± {overall_std_vf:.2f})')
        axs[1].set_xlabel('Test Cycle')
        axs[1].set_ylabel('Vf')
        axs[1].set_xlim(0.5, 5.5)
        axs[1].grid(True, alpha=0.3)
        axs[1].axhline(y=overall_mean_vf, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[1].axhline(y=overall_mean_vf + 2*overall_std_vf, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[1].axhline(y=overall_mean_vf - 2*overall_std_vf, color='orange', linestyle=':', alpha=0.5)
        
        # Plot Ith
        axs[2].set_title(f'Ith over Test (Mean: {overall_mean_ith:.2f} ± {overall_std_ith:.2f})')
        axs[2].set_xlabel('Test Cycle')
        axs[2].set_ylabel('Ith')
        axs[2].set_xlim(0.5, 5.5)
        axs[2].grid(True, alpha=0.3)
        axs[2].axhline(y=overall_mean_ith, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[2].axhline(y=overall_mean_ith + 2*overall_std_ith, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[2].axhline(y=overall_mean_ith - 2*overall_std_ith, color='orange', linestyle=':', alpha=0.5)
        
        # Plot each channel
        for ch in sorted(self.channels_data.keys()):
            data = self.channels_data[ch]
            
            # Determine if channel is outlier and style accordingly
            is_outlier_pf = ch in outliers_pf
            is_outlier_vf = ch in outliers_vf
            is_outlier_ith = ch in outliers_ith
            
            # Only show label for outliers
            label_pf = f'Channel {ch} (outlier)' if is_outlier_pf else None
            label_vf = f'Channel {ch} (outlier)' if is_outlier_vf else None
            label_ith = f'Channel {ch} (outlier)' if is_outlier_ith else None
            
            line_style = '-' if not is_outlier_pf else '--'
            line_width = 2 if not is_outlier_pf else 3
            axs[0].plot(test_cycles, data['pf'], marker='o', label=label_pf, 
                       linewidth=line_width, linestyle=line_style, 
                       markeredgewidth=2 if is_outlier_pf else 1,
                       markeredgecolor='red' if is_outlier_pf else None)
            
            line_style = '-' if not is_outlier_vf else '--'
            line_width = 2 if not is_outlier_vf else 3
            axs[1].plot(test_cycles, data['vf'], marker='o', label=label_vf, 
                       linewidth=line_width, linestyle=line_style,
                       markeredgewidth=2 if is_outlier_vf else 1,
                       markeredgecolor='red' if is_outlier_vf else None)
            
            line_style = '-' if not is_outlier_ith else '--'
            line_width = 2 if not is_outlier_ith else 3
            axs[2].plot(test_cycles, data['ith'], marker='o', label=label_ith, 
                       linewidth=line_width, linestyle=line_style,
                       markeredgewidth=2 if is_outlier_ith else 1,
                       markeredgecolor='red' if is_outlier_ith else None)
        
        axs[0].legend(loc='best', fontsize=8)
        axs[1].legend(loc='best', fontsize=8)
        axs[2].legend(loc='best', fontsize=8)
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return f'data:image/png;base64,{image_base64}'
    
    def _generate_single_channel_plot(self, channel):
        """Generate plot for a single channel"""
        if channel not in self.channels_data:
            return None
        
        data = self.channels_data[channel]
        test_cycles = [1, 2, 3, 4, 5]
        fig, axs = plt.subplots(3, 1, figsize=(8, 12))
        
        # Calculate statistics
        channel_means = {'pf': {}, 'vf': {}, 'ith': {}}
        for ch in self.channels_data.keys():
            channel_means['pf'][ch] = np.mean(self.channels_data[ch]['pf'])
            channel_means['vf'][ch] = np.mean(self.channels_data[ch]['vf'])
            channel_means['ith'][ch] = np.mean(self.channels_data[ch]['ith'])
        
        overall_mean_pf = np.mean(list(channel_means['pf'].values()))
        overall_std_pf = np.std(list(channel_means['pf'].values()))
        overall_mean_vf = np.mean(list(channel_means['vf'].values()))
        overall_std_vf = np.std(list(channel_means['vf'].values()))
        overall_mean_ith = np.mean(list(channel_means['ith'].values()))
        overall_std_ith = np.std(list(channel_means['ith'].values()))
        
        # Check if this channel is an outlier
        outlier_threshold = 2
        is_outlier_pf = abs(channel_means['pf'][channel] - overall_mean_pf) > outlier_threshold * overall_std_pf
        is_outlier_vf = abs(channel_means['vf'][channel] - overall_mean_vf) > outlier_threshold * overall_std_vf
        is_outlier_ith = abs(channel_means['ith'][channel] - overall_mean_ith) > outlier_threshold * overall_std_ith
        
        # Plot Pf
        title_suffix_pf = " ⚠️ OUTLIER" if is_outlier_pf else ""
        axs[0].set_title(f'Pf over Test Cycles - Channel {channel}{title_suffix_pf}')
        axs[0].set_xlabel('Test Cycle')
        axs[0].set_ylabel('Pf')
        axs[0].axhline(y=overall_mean_pf, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[0].axhline(y=overall_mean_pf + 2*overall_std_pf, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[0].axhline(y=overall_mean_pf - 2*overall_std_pf, color='orange', linestyle=':', alpha=0.5)
        axs[0].plot(test_cycles, data['pf'], marker='o', linewidth=2, color='#667eea', 
                   markeredgewidth=2 if is_outlier_pf else 1,
                   markeredgecolor='red' if is_outlier_pf else None, markersize=8)
        axs[0].grid(True, alpha=0.3)
        axs[0].legend(loc='best')
        
        # Plot Vf
        title_suffix_vf = " ⚠️ OUTLIER" if is_outlier_vf else ""
        axs[1].set_title(f'Vf over Test Cycles - Channel {channel}{title_suffix_vf}')
        axs[1].set_xlabel('Test Cycle')
        axs[1].set_ylabel('Vf')
        axs[1].axhline(y=overall_mean_vf, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[1].axhline(y=overall_mean_vf + 2*overall_std_vf, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[1].axhline(y=overall_mean_vf - 2*overall_std_vf, color='orange', linestyle=':', alpha=0.5)
        axs[1].plot(test_cycles, data['vf'], marker='o', linewidth=2, color='#764ba2',
                   markeredgewidth=2 if is_outlier_vf else 1,
                   markeredgecolor='red' if is_outlier_vf else None, markersize=8)
        axs[1].grid(True, alpha=0.3)
        axs[1].legend(loc='best')
        
        # Plot Ith
        title_suffix_ith = " ⚠️ OUTLIER" if is_outlier_ith else ""
        axs[2].set_title(f'Ith over Test Cycles - Channel {channel}{title_suffix_ith}')
        axs[2].set_xlabel('Test Cycle')
        axs[2].set_ylabel('Ith')
        axs[2].axhline(y=overall_mean_ith, color='red', linestyle='--', alpha=0.5, label='Overall Mean')
        axs[2].axhline(y=overall_mean_ith + 2*overall_std_ith, color='orange', linestyle=':', alpha=0.5, label='±2σ')
        axs[2].axhline(y=overall_mean_ith - 2*overall_std_ith, color='orange', linestyle=':', alpha=0.5)
        axs[2].plot(test_cycles, data['ith'], marker='o', linewidth=2, color='#f093fb',
                   markeredgewidth=2 if is_outlier_ith else 1,
                   markeredgecolor='red' if is_outlier_ith else None, markersize=8)
        axs[2].grid(True, alpha=0.3)
        axs[2].legend(loc='best')
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return f'data:image/png;base64,{image_base64}'
    
    def plot_channel(self, channel):
        """Generate plot for a specific channel or all channels"""
        try:
            if channel == 'all':
                plot_image = self._generate_all_channels_plot()
            else:
                plot_image = self._generate_single_channel_plot(int(channel))
                if plot_image is None:
                    return {'success': False, 'error': f'Channel {channel} not found'}
            
            return {
                'success': True,
                'plot': plot_image,
                'channel': channel
            }
        except Exception as e:
            import traceback
            return {'success': False, 'error': f'{str(e)}\n{traceback.format_exc()}'}
    
    def select_board(self, board):
        """Switch to a specific board"""
        try:
            board_num = int(board)
            if board_num not in self.boards_data:
                return {'success': False, 'error': f'Board {board} not found'}
            
            # Update current channels_data to selected board
            self.channels_data = self.boards_data[board_num]
            
            # Generate plot for all channels of this board
            plot_image = self._generate_all_channels_plot()
            
            return {
                'success': True,
                'plot': plot_image,
                'channels': list(self.channels_data.keys()),
                'currentBoard': board_num
            }
        except Exception as e:
            import traceback
            return {'success': False, 'error': f'{str(e)}\n{traceback.format_exc()}'}
    
    def analyze(self):
        """Analyze the selected folders"""
        folders = self.selected_folders
        
        if len(folders) != 5:
            return {'success': False, 'error': 'Need exactly 5 folders'}
        
        try:
            board_ch_csv_list = {}  # {board: {ch: [csv_paths]}}
            for test_cycle in range(1, 6):
                folder_path = folders[test_cycle - 1]
                subfolder = os.path.join(folder_path, f"{os.path.basename(folder_path)}-1")
                
                if not os.path.exists(subfolder):
                    return {
                        'success': False, 
                        'error': f'Subfolder {subfolder} not found for Test Cycle {test_cycle}'
                    }
                
                csv_files = [f for f in os.listdir(subfolder) if f.endswith('.csv')]
                if not csv_files:
                    return {
                        'success': False,
                        'error': f'No CSV files found in {subfolder}'
                    }
                
                for ch_csv in csv_files:
                    # Extract board number
                    board = (ch_csv.split("_")[0][5:])
                    # Extract channel number
                    ch = int((ch_csv.split("_")[-1].split(".")[0])[2:])
                    
                    if board not in board_ch_csv_list:
                        board_ch_csv_list[board] = {}
                    if ch not in board_ch_csv_list[board]:
                        board_ch_csv_list[board][ch] = [None]
                    board_ch_csv_list[board][ch].append(os.path.join(subfolder, ch_csv))
            
            # Collect data for all boards and channels
            self.boards_data = {}
            for board in sorted(board_ch_csv_list.keys()):
                self.boards_data[board] = {}
                for ch in sorted(board_ch_csv_list[board].keys()):
                    temp_summary = collect_data_with_test_cycle({i: board_ch_csv_list[board][ch][i] for i in range(1, 6)})
                    vf = []
                    pf = []
                    ith = []
                    for test_cycle in range(1, 6):
                        vf.append(temp_summary[test_cycle]["Vf"])
                        pf.append(temp_summary[test_cycle]["Pf"])
                        ith.append(temp_summary[test_cycle]["ith"])
                    
                    self.boards_data[board][ch] = {
                        'vf': vf,
                        'pf': pf,
                        'ith': ith
                    }
            
            # Set first board as default for display
            first_board = sorted(self.boards_data.keys())[0]
            self.channels_data = self.boards_data[first_board]
            
            # Generate plot for all channels of first board
            plot_image = self._generate_all_channels_plot()
            
            return {
                'success': True,
                'plot': plot_image,
                'boards': list(self.boards_data.keys()),
                'channels': list(self.channels_data.keys()),
                'currentBoard': first_board
            }
            
        except Exception as e:
            import traceback
            return {'success': False, 'error': f'{str(e)}\n{traceback.format_exc()}'}

def get_html():
    return '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Cycle Data Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .content {
            padding: 30px;
        }
        
        .folder-browser {
            margin-bottom: 30px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .browser-header {
            background: #f5f5f5;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .browser-header button {
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .browser-header button:hover {
            background: #5568d3;
        }
        
        .current-path {
            flex: 1;
            padding: 8px 12px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: monospace;
            font-size: 13px;
        }
        
        .folder-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .folder-item {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
        }
        
        .folder-item:hover {
            background: #f8f8f8;
        }
        
        .folder-item.selected {
            background: #e3f2fd;
            border-left: 3px solid #667eea;
        }
        
        .folder-icon {
            font-size: 20px;
        }
        
        .selected-folders {
            margin: 20px 0;
        }
        
        .selected-folders h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .folder-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            min-height: 40px;
        }
        
        .chip {
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        
        .chip .remove-btn {
            background: rgba(255,255,255,0.3);
            border: none;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
        }
        
        .chip .remove-btn:hover {
            background: rgba(255,255,255,0.5);
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .btn {
            padding: 12px 30px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            font-weight: 500;
            display: none;
        }
        
        .status.info {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .status.success {
            background: #e8f5e9;
            color: #388e3c;
        }
        
        .status.error {
            background: #ffebee;
            color: #d32f2f;
        }
        
        .channel-selector {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        
        .channel-selector.show {
            display: block;
        }
        
        .channel-selector h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .board-selector {
            margin: 20px 0;
            padding: 20px;
            background: #fff3e0;
            border-radius: 10px;
            display: none;
        }
        
        .board-selector.show {
            display: block;
        }
        
        .board-selector h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .selector-row {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .selector-row label {
            font-weight: 600;
            min-width: 80px;
        }
        
        .selector-row select {
            flex: 1;
            padding: 10px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            background: white;
        }
        
        .channel-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .channel-btn {
            padding: 10px 20px;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .channel-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        .channel-btn.active {
            background: #667eea;
            color: white;
        }
        
        .results {
            margin-top: 30px;
        }
        
        .plot-container {
            margin-bottom: 30px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .plot-header {
            background: #f5f5f5;
            padding: 15px;
            font-weight: 600;
            font-size: 18px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .plot-image {
            width: 100%;
            display: block;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Test Cycle Data Analyzer</h1>
            <p>選擇 5 個測試週期資料夾並分析數據</p>
        </div>
        
        <div class="content">
            <div class="folder-browser">
                <div class="browser-header">
                    <button onclick="goToParent()">⬆️ 上一層</button>
                    <button onclick="goToHome()">🏠 Home</button>
                    <input type="text" class="current-path" id="currentPath" readonly>
                </div>
                <div class="folder-list" id="folderList"></div>
            </div>
            
            <div class="selected-folders">
                <h3>已選擇的資料夾 (<span id="folderCount">0</span>/5)</h3>
                <div class="folder-chips" id="selectedFolders"></div>
            </div>
            
            <div id="status" class="status"></div>
            
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="clearSelection()">清除全部</button>
                <button class="btn btn-primary" id="analyzeBtn" onclick="analyze()" disabled>開始分析</button>
            </div>
            
            <div class="board-selector" id="boardSelector">
                <h3>📋 選擇 Board</h3>
                <div class="selector-row">
                    <label for="boardSelect">Board:</label>
                    <select id="boardSelect" onchange="onBoardChange()">
                    </select>
                </div>
            </div>
            
            <div class="channel-selector" id="channelSelector">
                <h3>選擇通道查看</h3>
                <div class="channel-buttons" id="channelButtons"></div>
            </div>
            
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        let currentPath = '';
        let selectedFolders = [];
        
        async function loadFolders(path = null) {
            try {
                const data = await pywebview.api.list_folders(path);
                
                if (data.success) {
                    currentPath = data.currentPath;
                    document.getElementById('currentPath').value = currentPath;
                    
                    const folderList = document.getElementById('folderList');
                    folderList.innerHTML = '';
                    
                    data.items.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'folder-item';
                        div.innerHTML = `<span class="folder-icon">📁</span><span>${item.name}</span>`;
                        
                        div.onclick = (e) => {
                            if (e.detail === 1) {
                                toggleSelection(item.path);
                            } else if (e.detail === 2) {
                                loadFolders(item.path);
                            }
                        };
                        
                        if (selectedFolders.includes(item.path)) {
                            div.classList.add('selected');
                        }
                        
                        folderList.appendChild(div);
                    });
                } else {
                    showStatus('載入資料夾錯誤: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('載入資料夾錯誤: ' + error.message, 'error');
            }
        }
        
        async function toggleSelection(path) {
            const index = selectedFolders.indexOf(path);
            if (index > -1) {
                const result = await pywebview.api.remove_folder(index);
                if (result.success) {
                    selectedFolders = result.folders;
                }
            } else {
                const result = await pywebview.api.select_folder(path);
                if (result.success) {
                    selectedFolders = result.folders;
                } else {
                    showStatus(result.error, 'error');
                }
            }
            updateSelectedDisplay();
            loadFolders(currentPath);
        }
        
        function updateSelectedDisplay() {
            const container = document.getElementById('selectedFolders');
            container.innerHTML = '';
            
            selectedFolders.forEach((path, index) => {
                const chip = document.createElement('div');
                chip.className = 'chip';
                const folderName = path.split('/').pop();
                chip.innerHTML = `
                    <span>${index + 1}. ${folderName}</span>
                    <button class="remove-btn" onclick="removeFolder(${index})">×</button>
                `;
                container.appendChild(chip);
            });
            
            document.getElementById('folderCount').textContent = selectedFolders.length;
            document.getElementById('analyzeBtn').disabled = selectedFolders.length !== 5;
        }
        
        async function removeFolder(index) {
            const result = await pywebview.api.remove_folder(index);
            if (result.success) {
                selectedFolders = result.folders;
                updateSelectedDisplay();
                loadFolders(currentPath);
            }
        }
        
        async function clearSelection() {
            const result = await pywebview.api.clear_folders();
            if (result.success) {
                selectedFolders = [];
                updateSelectedDisplay();
                loadFolders(currentPath);
            }
        }
        
        function goToParent() {
            const parent = currentPath.split('/').slice(0, -1).join('/') || '/';
            loadFolders(parent);
        }
        
        function goToHome() {
            loadFolders();
        }
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.className = `status ${type}`;
            status.textContent = message;
            status.style.display = 'block';
            
            if (type === 'success' || type === 'error') {
                setTimeout(() => {
                    status.style.display = 'none';
                }, 5000);
            }
        }
        
        async function analyze() {
            if (selectedFolders.length !== 5) {
                showStatus('請選擇恰好 5 個資料夾', 'error');
                return;
            }
            
            const results = document.getElementById('results');
            results.innerHTML = '<div class="loading"><div class="spinner"></div><p>分析數據中...</p></div>';
            showStatus('處理數據中...', 'info');
            
            try {
                const data = await pywebview.api.analyze();
                
                if (data.success) {
                    showStatus(`分析完成！找到 ${data.boards.length} 個 Boards, ${data.channels.length} 個通道`, 'success');
                    
                    // Show board selector
                    const boardSelector = document.getElementById('boardSelector');
                    boardSelector.classList.add('show');
                    
                    // Populate board dropdown
                    const boardSelect = document.getElementById('boardSelect');
                    boardSelect.innerHTML = '';
                    data.boards.forEach(board => {
                        const option = document.createElement('option');
                        option.value = board;
                        option.textContent = `Board ${board}`;
                        if (board === data.currentBoard) {
                            option.selected = true;
                        }
                        boardSelect.appendChild(option);
                    });
                    
                    // Show channel selector
                    const channelSelector = document.getElementById('channelSelector');
                    channelSelector.classList.add('show');
                    
                    // Create channel buttons
                    updateChannelButtons(data.channels);
                    
                    // Display initial plot (all channels of current board)
                    results.innerHTML = `
                        <div class="plot-container">
                            <div class="plot-header">Board ${data.currentBoard} - 所有通道 (Channels: ${data.channels.join(', ')})</div>
                            <img src="${data.plot}" class="plot-image" alt="All channels plot">
                        </div>
                    `;
                } else {
                    showStatus('錯誤: ' + data.error, 'error');
                    results.innerHTML = '';
                }
            } catch (error) {
                showStatus('分析數據錯誤: ' + error.message, 'error');
                results.innerHTML = '';
            }
        }
        
        function updateChannelButtons(channels) {
            const channelButtons = document.getElementById('channelButtons');
            channelButtons.innerHTML = '';
            
            // Add "All Channels" button
            const allBtn = document.createElement('button');
            allBtn.className = 'channel-btn active';
            allBtn.textContent = '所有通道';
            allBtn.onclick = () => selectChannel('all');
            channelButtons.appendChild(allBtn);
            
            // Add individual channel buttons
            channels.forEach(ch => {
                const btn = document.createElement('button');
                btn.className = 'channel-btn';
                btn.textContent = `Channel ${ch}`;
                btn.onclick = () => selectChannel(ch);
                channelButtons.appendChild(btn);
            });
        }
        
        async function onBoardChange() {
            const boardSelect = document.getElementById('boardSelect');
            const selectedBoard = boardSelect.value;
            
            const results = document.getElementById('results');
            results.innerHTML = '<div class="loading"><div class="spinner"></div><p>切換 Board 中...</p></div>';
            showStatus('載入 Board 數據中...', 'info');
            
            try {
                const data = await pywebview.api.select_board(selectedBoard);
                
                if (data.success) {
                    showStatus(`已切換到 Board ${selectedBoard}`, 'success');
                    
                    // Update channel buttons
                    updateChannelButtons(data.channels);
                    
                    // Display plot for all channels of new board
                    results.innerHTML = `
                        <div class="plot-container">
                            <div class="plot-header">Board ${selectedBoard} - 所有通道 (Channels: ${data.channels.join(', ')})</div>
                            <img src="${data.plot}" class="plot-image" alt="All channels plot">
                        </div>
                    `;
                } else {
                    showStatus('錯誤: ' + data.error, 'error');
                    results.innerHTML = '';
                }
            } catch (error) {
                showStatus('切換 Board 錯誤: ' + error.message, 'error');
            }
        }
        
        async function selectChannel(channel) {
            // Update button states
            const buttons = document.querySelectorAll('.channel-btn');
            buttons.forEach(btn => {
                btn.classList.remove('active');
                if ((channel === 'all' && btn.textContent === '所有通道') ||
                    (channel !== 'all' && btn.textContent === `Channel ${channel}`)) {
                    btn.classList.add('active');
                }
            });
            
            // Show loading
            const results = document.getElementById('results');
            results.innerHTML = '<div class="loading"><div class="spinner"></div><p>生成圖表中...</p></div>';
            
            try {
                const data = await pywebview.api.plot_channel(channel);
                
                if (data.success) {
                    const boardSelect = document.getElementById('boardSelect');
                    const currentBoard = boardSelect.value;
                    const title = channel === 'all' ? `Board ${currentBoard} - 所有通道` : `Board ${currentBoard} - Channel ${channel}`;
                    results.innerHTML = `
                        <div class="plot-container">
                            <div class="plot-header">${title}</div>
                            <img src="${data.plot}" class="plot-image" alt="Plot for ${title}">
                        </div>
                    `;
                } else {
                    showStatus('錯誤: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('生成圖表錯誤: ' + error.message, 'error');
            }
        }
        
        // Initialize when window is ready
        window.addEventListener('pywebviewready', function() {
            loadFolders();
        });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    api = API()
    window = webview.create_window(
        'Test Cycle Data Analyzer',
        html=get_html(),
        js_api=api,
        width=1200,
        height=900
    )
    webview.start(debug=False)
