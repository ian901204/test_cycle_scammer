import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Reusable thread pool for CSV reading - created once, reused across calls
_executor = None

def _get_executor():
    global _executor
    if _executor is None:
        import os
        # Use number of CPUs, but cap at 8 to avoid overwhelming the system
        max_workers = min(os.cpu_count() or 4, 8)
        _executor = ThreadPoolExecutor(max_workers=max_workers)
    return _executor

def _read_single_csv(args):
    """Read a single CSV file and return raw data. Runs in thread pool."""
    path, test_cycle = args
    result = {
        'test_cycle': test_cycle,
        'cur': [], 'power': [], 'voltage': [],
        'vf': 0, 'pf': 0, 'date': '', 'ith': 0
    }
    try:
        with open(path, "r") as f:
            reader = csv.reader(f)
            data = list(reader)
            result['date'] = data[1][0].split(" ")[-2]
            data = data[9:]
            for row in data:
                cur_val = float(row[0])
                power_val = float(row[1])
                voltage_val = float(row[2])
                result['cur'].append(cur_val)
                result['power'].append(power_val)
                result['voltage'].append(voltage_val)
                if cur_val == 7.5:
                    result['vf'] = voltage_val
                    result['pf'] = power_val
        # Calculate Ith using linear regression on filtered data (power 100-500)
        ith_cur = [result['cur'][i] for i in range(len(result['cur'])) if 500 >= result['power'][i] >= 100]
        ith_pow = [result['power'][i] for i in range(len(result['power'])) if 500 >= result['power'][i] >= 100]
        ith_corr = CalIth(ith_cur, ith_pow)
        result['ith'] = -ith_corr[1] / ith_corr[0] if ith_corr[0] != 0 else 0
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return result


def collect_data_with_test_cycle(path_list: dict):
    """
    Read 5 CSV files in parallel using thread pool.
    path_list: dict with keys 1-5 mapping to file paths.
    Returns: dict with keys 1-5 containing summary data for each test cycle.
    """
    executor = _get_executor()

    # Submit all 5 CSV reads in parallel
    args_list = [(path_list[tc], tc) for tc in range(1, 6)]
    futures = {executor.submit(_read_single_csv, args): args for args in args_list}

    temp_summary = {x: {} for x in range(1, 6)}

    # Collect results as they complete
    for future in as_completed(futures):
        result = future.result()
        tc = result['test_cycle']
        temp_summary[tc] = {
            'Cur': result['cur'],
            'Power': result['power'],
            'Voltage': result['voltage'],
            'Vf': result['vf'],
            'Pf': result['pf'],
            'ith': result['ith'],
            'date': result['date'],
            'ithCor': [0, 0],
            'fpoint': 0
        }

    return temp_summary


def CalIth(LD, PD):
    """
    Calculate the Ith value using the given LD and PD lists.

    Parameters:
    LD (list): A list of LD values.
    PD (list): A list of PD values.

    Returns:
    list: A list containing the calculated values of m and b.
    """
    try:
        if len(LD) != len(PD):
            print("Length of LD and PD is not equal")
            return [0, 0]
        LDSum = sum(LD)
        PDSum = sum(PD)
        LDtimePD = [LD[i]*PD[i] for i in range(len(LD))]
        LDPDSum = sum(LDtimePD)
        LD2pow = [LD[i]**2 for i in range(len(LD))]
        LD2powsum = sum(LD2pow)
        n = len(LD)
        m = ((LDPDSum*n) - (LDSum*PDSum))/(n*(LD2powsum) - LDSum**2)
        b = (PDSum/n - (m*LDSum/n))
    except Exception as e:
        print("Error in Ith Calculation", e)
        m = 0
        b = 0
    return [m, b]