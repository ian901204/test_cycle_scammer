import csv

def collect_data_with_test_cycle(path_list: dict):
    #this is a path list for multiple files
    temp_summary = {x:{} for x in range(1,6)}
    result_summary = {"Cur": [], "Power": [], "Voltage": [], "ith": 0, "ithCor": [0, 0], "Vf": 0, "Pf": 0, "date":"", "fpoint":0}
    try:
        for test_cycle in range(1,6):
            with open(path_list[test_cycle], "r") as f:
                temp_summary[test_cycle] = {}
                ithD = {"Cur":[], "Power": []}
                summary = {"Cur": [], "Power": [], "Voltage": [], "ith": 0, "ithCor": [0, 0], "Vf": 0, "Pf": 0, "date":"", "fpoint":0}
                reader = csv.reader(f)
                data = list(reader)
                summary["date"] = data[1][0].split(" ")[-2]
                data = data[9:]
                for row in data:
                    summary["Cur"].append(float(row[0]))
                    summary["Power"].append(float(row[1]))
                    summary["Voltage"].append(float(row[2]))
                    if float(row[0]) == 7.5:
                        summary["fpoint"] = float(row[0])
                        summary["Vf"] = float(row[2])
                        summary["Pf"] = float(row[1])
                    if 500 >= float(row[1]) >= 100:
                        ithD["Cur"].append(float(row[0]))
                        ithD["Power"].append(float(row[1]))
                summary["ithCor"] = CalIth(ithD["Cur"], ithD["Power"])
                summary["ith"] = -summary["ithCor"][1] / summary["ithCor"][0]
                temp_summary[test_cycle] = summary
        #start calualte average
        temp_vf = []
        temp_pf = []
        temp_ith = []
        for test_cycle in range(1,6):
            temp_vf.append(temp_summary[test_cycle]["Vf"])
            temp_pf.append(temp_summary[test_cycle]["Pf"])
            temp_ith.append(temp_summary[test_cycle]["ith"])
        result_summary["Vf"] = sum(temp_vf)/len(temp_vf)
        result_summary["Pf"] = sum(temp_pf)/len(temp_pf)
        result_summary["ith"] = sum(temp_ith)/len(temp_ith)
        
    except FileNotFoundError:
        raise FileNotFoundError(f"File {path_list[test_cycle]} not found.")
    except Exception as e:
        print(f"Error reading file {path_list[test_cycle]}: {e.with_traceback()}")
        result_summary["ith"] = 0
        result_summary["Vf"] = 0
        result_summary["Pf"] = 0
    #as now only use all 5 test cycles test to plot the other code stay until we need it
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