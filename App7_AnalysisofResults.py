
import tkinter as tk
from tkinter import filedialog
import json
import os
from functions.io import print_agents

import numpy as np

import matplotlib.pyplot as plt


def select_results_folder():
    """Pop-up window to select the results folder."""
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    folder_selected = filedialog.askdirectory(title="Select Results Folder")
    return folder_selected










# Select the test folder
results_folder = select_results_folder()
result_files = [os.path.join(results_folder, f) for f in os.listdir(results_folder) if f.endswith('.json')]





test_results = []

# Run simulation for each test file
for result_file in result_files:
    
    with open(result_file) as file:
        data = json.load(file)

    # Append relevant fields to the test_results array
    test_results.append({
        "success_code": data["success_code"],
        "time": data["time"],
        "coverage": data["coverage"],
        "num_H_agents": data["num_H_agents"],
        "num_G_agents": data["num_G_agents"],
        "num_H_tasks": data["num_H_tasks"],
        "num_G_tasks": data["num_G_tasks"],
        "total_cells": data["total_cells"],
        "home_makespan": data["home_makespan"],
        "home_sumofcosts": data["home_sumofcosts"],
        "home_completedtasks": data["home_completedtasks"],
        "home_servicetime": data["home_servicetime"],
        "guest_makespan": data["guest_makespan"],
        "guest_completedtasks": data["guest_completedtasks"],
        "guest_sumofcosts": data["guest_sumofcosts"],
        "guest_servicetime": data["guest_servicetime"],
        "home_replan": data["home_replan"],
        "guest_replan": data["guest_replan"],
        "coexistance_coefficient": data["coexistance_coefficient"],
        "failure_message": data["failure_message"]
    })


success_1_count = 0
success_0_count = 0

total_home_makespan = 0
total_home_service_time = 0

total_guest_makespan = 0
total_guest_service_time = 0

total_total_makespan = 0
total_total_service_time = 0

total_coexistance_coefficient=0
total_home_replan = 0
total_guest_replan=0


count_total_completed_tasks = 0
test_count = len(result_files)

deadlock_count = 0
home_soft_lock_count = 0
guest_soft_lock_count = 0
collision_failure_count = 0

home_makespan_values = []
guest_makespan_values = []
total_makespan_values = []

home_service_time_values = []
guest_service_time_values = []
total_service_time_values = []


# Print common test information from any one result (assuming all are similar)
sample_result = test_results[0]
print(f"Coverage: {sample_result['coverage']} / {sample_result['total_cells']} = {100*(sample_result['coverage'] / sample_result['total_cells']):.2f}%")
print(f"H Agent Count: {sample_result['num_H_agents']}")
print(f"G Agent Count: {sample_result['num_G_agents']}")
print(f"H Task Count: {sample_result['num_H_tasks']}")
print(f"G Task Count: {sample_result['num_G_tasks']}")
print()



# Loop through the results to gather statistics
for result in test_results:
    # Success code counts
    if result["success_code"] == 1:
        success_1_count += 1



        home_makespan_values.append(result["home_makespan"])
        guest_makespan_values.append(result["guest_makespan"])
        total_makespan_values.append(max(result["home_makespan"] or 0, result["guest_makespan"] or 0))

        home_service_time_values.append(result["home_servicetime"])
        guest_service_time_values.append(result["guest_servicetime"])



        # Accumulate makespan and service time if available
        total_home_makespan += result["home_makespan"]
        total_guest_makespan += result["guest_makespan"]
        total_total_makespan += max(result["home_makespan"] or 0, result["guest_makespan"] or 0)
        

        total_home_service_time += result["home_servicetime"]
        total_guest_service_time += result["guest_servicetime"]

        total_coexistance_coefficient += result["coexistance_coefficient"]
        total_home_replan  += result["home_replan"]
        total_guest_replan += result["guest_replan"]

        # Calculate total service time for this test
        completed_tasks_sum = result["home_completedtasks"] + result["guest_completedtasks"]
        if completed_tasks_sum > 0:
            total_servicetime = (result["home_sumofcosts"] + result["guest_sumofcosts"]) / completed_tasks_sum
            total_total_service_time += total_servicetime
            total_service_time_values.append(total_servicetime)
    
    else:
        success_0_count += 1

        # Count each type of failure message
        failure_message = result["failure_message"]
        if failure_message == "Simulation Ends Because Guest Agents went into a deadlock.":
            deadlock_count += 1
        elif failure_message == "Simulation Ends Because Home Agents are Soft-Locked.":
            home_soft_lock_count += 1
        elif failure_message == "Simulation Ends Because Guest Agents are Soft-Locked.":
            guest_soft_lock_count += 1
        else:
            collision_failure_count += 1


# Calculations for averages


average_home_makespan = total_home_makespan / success_1_count if success_1_count > 0 else 0
average_guest_makespan = total_guest_makespan / success_1_count if success_1_count > 0 else 0
average_total_makespan = total_total_makespan / success_1_count if success_1_count > 0 else 0

average_home_service_time = total_home_service_time / success_1_count if success_1_count > 0 else 0
average_guest_service_time = total_guest_service_time / success_1_count if success_1_count > 0 else 0
average_total_service_time = total_total_service_time / success_1_count if success_1_count > 0 else 0

average_coexistance_coefficient = total_coexistance_coefficient / success_1_count if success_1_count > 0 else 0
average_home_replan = total_home_replan / success_1_count if success_1_count > 0 else 0
average_guest_replan = total_guest_replan / success_1_count if success_1_count > 0 else 0

std_home_makespan = np.std(home_makespan_values, ddof=1) if home_makespan_values else 0
std_guest_makespan = np.std(guest_makespan_values, ddof=1) if guest_makespan_values else 0
std_total_makespan = np.std(total_makespan_values, ddof=1) if total_makespan_values else 0

std_home_service_time = np.std(home_service_time_values, ddof=1) if home_service_time_values else 0
std_guest_service_time = np.std(guest_service_time_values, ddof=1) if guest_service_time_values else 0
std_total_service_time = np.std(total_service_time_values, ddof=1) if total_service_time_values else 0


# Print the computed statistics
print(f"Success rate: {success_1_count}/{test_count} = {success_1_count / test_count:.2f}")
print(f"Failure rate (Convenience): {success_0_count}/{test_count} = {success_0_count / test_count:.2f}")
if success_0_count:
    print(f"Guest Agents Deadlock Failures: {deadlock_count} / {success_0_count}")
    print(f"Home Agents Soft-Lock Failures: {home_soft_lock_count} / {success_0_count}")
    print(f"Guest Agents Soft-Lock Failures: {guest_soft_lock_count} / {success_0_count}")
    print(f"Collision Failures: {collision_failure_count} / {success_0_count}")

print()
print(f"Average home makespan: {average_home_makespan:.2f}")
print(f"Average home service time: {average_home_service_time:.2f}")
print()
print(f"Average guest makespan: {average_guest_makespan:.2f}")
print(f"Average guest service time: {average_guest_service_time:.2f}")
print()
print(f"Average total makespan: {average_total_makespan:.2f}")
print(f"Average total service time: {average_total_service_time:.2f}")
print()
print(f"Average coexistance coefficient: {average_coexistance_coefficient:.2f}")
print(f"Average number of home replans: {average_home_replan:.2f}")
print(f"Average number of guest replans: {average_guest_replan:.2f}")
print()
print(f"Standard Deviation home makespan: {std_home_makespan:.2f}")
print(f"Standard Deviation home service time: {std_home_service_time:.2f}")
print()
print(f"Standard Deviation guest makespan: {std_guest_makespan:.2f}")
print(f"Standard Deviation guest service time: {std_guest_service_time:.2f}")
print()
print(f"Standard Deviation total makespan: {std_total_makespan:.2f}")
print(f"Standard Deviation total service time: {std_total_service_time:.2f}")




# Gather home service times from successful test results
coexistance_coefficients = [result["coexistance_coefficient"] for result in test_results if result["success_code"] == 1]



# Initialize cumulative variables
cumulative_cv = []

# Calculate cumulative CV statistics
for i in range(1, len(coexistance_coefficients) + 1):
    # Calculate mean and standard deviation for the first i values
    current_mean = np.mean(coexistance_coefficients[:i])
    current_std_dev = np.std(coexistance_coefficients[:i], ddof=1)  # Sample std deviation with ddof=1
    current_cv = (current_std_dev / current_mean) * 100  # CV in percentage
    cumulative_cv.append(current_cv)
    

print("Final CV value:", cumulative_cv[-1])

# Plotting CV over increasing sample size to visualize stabilization
import matplotlib.pyplot as plt

plt.plot(range(1, len(coexistance_coefficients) + 1), cumulative_cv, label="CV of Coexistence Coefficient (%)")
plt.xlabel("Sample Size")
plt.ylabel("Coefficient of Variation (%)")
plt.title("Sample Size vs. Coefficient of Variation of Coexistence Coefficient")
plt.legend()
plt.show()