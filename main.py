import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

def chose_folders():
    folders = []
    
    root = tk.Tk()
    root.title("Select Test Cycle Folders")
    root.geometry("500x400")
    
    tk.Label(root, text="Click 'Add Folders' to select multiple folders at once.").pack(pady=5)
    
    # Listbox to display selected folders
    listbox = tk.Listbox(root, width=60, height=10)
    listbox.pack(pady=10)
    
    def add_folders():
        try:
            # Use AppleScript to select multiple folders on macOS
            script = '''
            set selectedFolders to choose folder with prompt "Select test cycle folders (hold Command to select multiple)" with multiple selections allowed
            set folderPaths to ""
            repeat with aFolder in selectedFolders
                set folderPaths to folderPaths & POSIX path of aFolder & ","
            end repeat
            return folderPaths
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and result.stdout.strip():
                # Remove trailing comma and split
                paths_str = result.stdout.strip().rstrip(',')
                selected_paths = [path.strip() for path in paths_str.split(',') if path.strip()]
                for path in selected_paths:
                    if path and path not in folders:
                        folders.append(path)
                        listbox.insert(tk.END, f"Folder {len(folders)}: {os.path.basename(path)}")
                update_status()
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "Folder selection timed out")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder dialog: {str(e)}\nPlease try again.")
    
    def remove_selected():
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            folders.pop(index)
            listbox.delete(index)
            # Renumber remaining items
            listbox.delete(0, tk.END)
            for i, folder in enumerate(folders, 1):
                listbox.insert(tk.END, f"Folder {i}: {os.path.basename(folder)}")
            update_status()
    
    def update_status():
        status_label.config(text=f"Selected {len(folders)} folders (need 5)")
        if len(folders) == 5:
            done_btn.config(state=tk.NORMAL, bg="green")
        else:
            done_btn.config(state=tk.DISABLED, bg="gray")
    
    def done():
        if len(folders) == 5:
            root.destroy()
        else:
            messagebox.showerror("Error", "Please select exactly 5 folders")
    
    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)
    
    tk.Button(btn_frame, text="Add Folders", command=add_folders).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=5)
    
    status_label = tk.Label(root, text="Selected 0 folders (need 5)")
    status_label.pack(pady=5)
    
    done_btn = tk.Button(root, text="Done", command=done, state=tk.DISABLED, bg="gray")
    done_btn.pack(pady=10)
    
    root.mainloop()
    return folders

def run_analysis():
    test_cycle_folders = chose_folders()
    if len(test_cycle_folders) != 5:
        messagebox.showerror("Error", "Need exactly 5 folders")
        return
    
    board_ch_csv_list = {}  # {board: {ch: [csv_paths]}}
    for test_cycle in range(1, 6):
        folder_path = test_cycle_folders[test_cycle - 1]
        subfolder = os.path.join(folder_path, f"{os.path.basename(folder_path)}-1")
        if not os.path.exists(subfolder):
            messagebox.showerror("Error", f"Subfolder {subfolder} not found for Test Cycle {test_cycle}")
            return
        try:
            csv_files = [f for f in os.listdir(subfolder) if f.endswith('.csv')]
            if not csv_files:
                messagebox.showerror("Error", f"No CSV files found in {subfolder}")
                return
            for ch_csv in csv_files:
                # Extract board number
                board = int(ch_csv.split("_")[0][5:])
                # Extract channel number
                ch = int((ch_csv.split("_")[-1].split(".")[0])[2:])
                
                if board not in board_ch_csv_list:
                    board_ch_csv_list[board] = {}
                if ch not in board_ch_csv_list[board]:
                    board_ch_csv_list[board][ch] = [None]
                board_ch_csv_list[board][ch].append(os.path.join(subfolder, ch_csv))
        except Exception as e:
            messagebox.showerror("Error", f"Error processing folder for Test Cycle {test_cycle}: {str(e)}")
            return
    
    # Process each board and channel
    board_data = {}
    skipped_channels = []
    
    for board in board_ch_csv_list:
        board_data[board] = {}
        for ch in board_ch_csv_list[board]:
            try:
                from scan import collect_data_with_test_cycle
                temp_summary = collect_data_with_test_cycle({i: board_ch_csv_list[board][ch][i] for i in range(1, 6)})
                vf = []
                pf = []
                ith = []
                for test_cycle in range(1, 6):
                    vf.append(temp_summary[test_cycle]["Vf"])
                    pf.append(temp_summary[test_cycle]["Pf"])
                    ith.append(temp_summary[test_cycle]["ith"])
                board_data[board][ch] = {"vf": vf, "pf": pf, "ith": ith}
            except Exception as e:
                # Skip problematic channel and continue
                skipped_channels.append(f"Board {board} Channel {ch}")
                print(f"Warning: Skipping Board {board} Channel {ch} due to error: {str(e)}")
                continue
    
    # Remove empty boards
    board_data = {board: channels for board, channels in board_data.items() if channels}
    
    if not board_data:
        messagebox.showerror("Error", f"No valid data found. All channels failed.")
        return
    
    from plotter import plot_basic
    # For simplicity, plot data from first board
    if board_data:
        first_board = sorted(board_data.keys())[0]
        plot_basic(board_data[first_board])
    
    success_msg = f"Analysis completed! Found {len(board_data)} boards"
    if skipped_channels:
        success_msg += f"\n\n⚠️ Skipped {len(skipped_channels)} problematic channels:\n" + "\n".join(skipped_channels[:5])
        if len(skipped_channels) > 5:
            success_msg += f"\n... and {len(skipped_channels) - 5} more"
    
    messagebox.showinfo("Success", success_msg)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test Cycle Scammer")
    root.geometry("400x200")
    
    tk.Label(root, text="Test Cycle Data Analyzer", font=("Arial", 16)).pack(pady=10)
    tk.Label(root, text="Click 'Start Analysis' to select 5 test cycle folders\nand analyze the data.", justify=tk.CENTER).pack(pady=5)
    tk.Button(root, text="Start Analysis", command=run_analysis, font=("Arial", 12)).pack(pady=10)
    tk.Button(root, text="Quit", command=root.quit).pack(pady=5)
    
    root.mainloop()