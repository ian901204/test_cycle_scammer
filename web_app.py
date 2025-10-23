import os
from flask import Flask, render_template, request, jsonify, send_file
import json
from scan import collect_data_with_test_cycle
from plotter import plot_basic
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list_folders', methods=['POST'])
def list_folders():
    """List folders in a given directory"""
    data = request.json
    path = data.get('path', os.path.expanduser('~'))
    
    try:
        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                items.append({
                    'name': item,
                    'path': full_path,
                    'isDirectory': True
                })
        items.sort(key=lambda x: x['name'].lower())
        return jsonify({
            'success': True,
            'currentPath': path,
            'parent': os.path.dirname(path) if path != '/' else None,
            'items': items
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze the selected folders"""
    data = request.json
    folders = data.get('folders', [])
    
    if len(folders) != 5:
        return jsonify({'success': False, 'error': 'Need exactly 5 folders'})
    
    try:
        ch_csv_list = {}
        for test_cycle in range(1, 6):
            folder_path = folders[test_cycle - 1]
            subfolder = os.path.join(folder_path, f"{os.path.basename(folder_path)}-1")
            
            if not os.path.exists(subfolder):
                return jsonify({
                    'success': False, 
                    'error': f'Subfolder {subfolder} not found for Test Cycle {test_cycle}'
                })
            
            csv_files = [f for f in os.listdir(subfolder) if f.endswith('.csv')]
            if not csv_files:
                return jsonify({
                    'success': False,
                    'error': f'No CSV files found in {subfolder}'
                })
            
            for ch_csv in csv_files:
                ch = int((ch_csv.split("_")[-1].split(".")[0])[2:])
                if ch not in ch_csv_list:
                    ch_csv_list[ch] = [None]
                ch_csv_list[ch].append(os.path.join(subfolder, ch_csv))
        
        # Generate plots for each channel
        plots = []
        for ch in ch_csv_list:
            temp_summary = collect_data_with_test_cycle({i: ch_csv_list[ch][i] for i in range(1, 6)})
            vf = []
            pf = []
            ith = []
            for test_cycle in range(1, 6):
                vf.append(temp_summary[test_cycle]["Vf"])
                pf.append(temp_summary[test_cycle]["Pf"])
                ith.append(temp_summary[test_cycle]["ith"])
            
            # Create plot
            test_cycles = [1, 2, 3, 4, 5]
            fig, axs = plt.subplots(3, 1, figsize=(8, 12))
            
            axs[0].set_title(f'Pf over Test Cycles - Channel {ch}')
            axs[0].set_xlabel('Test Cycle')
            axs[0].set_ylabel('Pf')
            axs[0].plot(test_cycles, pf, marker='o')
            
            axs[1].set_title(f'Vf over Test Cycles - Channel {ch}')
            axs[1].set_xlabel('Test Cycle')
            axs[1].set_ylabel('Vf')
            axs[1].plot(test_cycles, vf, marker='o')
            
            axs[2].set_title(f'Ith over Test Cycles - Channel {ch}')
            axs[2].set_xlabel('Test Cycle')
            axs[2].set_ylabel('Ith')
            axs[2].plot(test_cycles, ith, marker='o')
            
            plt.tight_layout()
            
            # Convert plot to base64 image
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            plots.append({
                'channel': ch,
                'image': f'data:image/png;base64,{image_base64}',
                'data': {
                    'vf': vf,
                    'pf': pf,
                    'ith': ith
                }
            })
        
        return jsonify({
            'success': True,
            'plots': plots
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
