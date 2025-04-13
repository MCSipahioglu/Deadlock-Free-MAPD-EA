
# 1. Installation
- This repo contains all the code to create test cases and run simulations. However the maps are hosted elsewhere since the map files are too big to be uploaded to github.
- Download the map files from [MEGA](https://mega.nz/folder/vEhmXBjR#hFl6UpluiUyJg0c7lMGI1Q) and replace the Folder Standard Maps with the downloaded folder.

# 2. Available Software
1. **App1_MapDrawer**
Output: Map File
Input: None.
Use: Set the map's max size using the sidebar. Draw the map with Left Click, erase the map with Right Click. Export the map file when done. (If there are an excess of black cells around the drawn map, they are trimmed automatically.)

2. **App2B_DrawPartitions**
Output: Partitioned Map File
Input: Map File or a Partitioned Map File
Use: Choose a color from the sidebar and paint the partitions manually, shades of green can be used to draw the locations guest agents can access (tiling), shades of red can be used to draw the locations guest agents cant access, and blue can be used to draw parking locations which cant be accessed by the guest agents and will be used by the home agents as resting points if there are no tasks left when using my algorithm.
Note: **App2_MapPartitioner** calculates all possible partitionings automatically and can be used to select and export the partitioned map file, HOWEVER it uses brute force to do this which means even for a small map of about 10x10 it will take close to 2 hours to conclude, this app is not recommended to be used for map partitioning without optimizing its software first.


3. **App3_AgentPlacer**
Output: Map File with Agents
Input: Partitioned Map File or Map File with Agents
Use: Right Click to place a home agent, Left Click to place a guest agent. You can remove an agent by clicking on it with the same button you placed it with.

4. **App4_TaskGenerator**
Output: Test Case
Input: Map File with Agents
Use: On the sidebar write the number of tasks you want to generate for each team. Click Randomly Add ... Tasks to add that many tasks, home tasks are added between any two points in the map, guest tasks are added between any two points in the tiling.

5. **App5_BulkTestGenerator**
Output: A Setting File and many Test Cases
Input: Partitioned Map File or Map File with Agents
Use: Follow the instructions in the console.
- Currently the way BulkTestGenerator creates different test cases is that it first gets the agent counts and places both agent types into the partition. If home agents are wanted to be placed outside of the partition as well line 47 should be uncommented and line 48 should be commented instead.
- After placing the agents the task per agent count is inputted and the home and guest task counts are calculated as per lines 382-383 which can be changed to allow more customization.
- Having calculated the total number of tasks required for each team, a set of pickup/delivery points are chosen to be sampled upon, currently simply all cells in the partition are chosen to be sampled from to create a task start and goal point. (Home and Guest Pickup/Delivery Points stored under H_Delivery_Points and G_Delivery_Points are stored in the settings file which allows for tasks to be created from the same set of start and goal points as discussed in bullet point 4. ==A way to manually set task start or end points currently do not exist since it was not needed for my algorithm.==)
- The desired number of tasks for each team are generated from sampling two random elements from H_Delivery_Points or G_Delivery_Points.
- After creating a single test case, other test cases are created until the desired number of test cases is reached by re-generating the tasks without changing the agent placement.

6. **Simulate**, **Simulate_combined_team**
Input: A test case
Use: Import a test case. Each time-step is executed in two steps first all the moves for that time-step are calculated and shown and then these moves are executed. This can be triggered manually by clicking Step Forward on the sidebar. Alternatively you can click Play to step forward automatically until the simulation ends or you click Pause.
Output: The simulation result displayed on screen upon completion

 6. **App6_BulkTestExecutor**, **App6_BulkTestExecutor_Combined**
Input: The folder containing many test cases.
Output: The simulation results for each of these test cases.

- **Simulate_combined_team** and **App6_BulkTestExecutor_Combined** exist to handle the case where we consider the two teams acting as one (No need for observations to know other teams' agents' locations.)

7. **App7_AnalysisofResults**
Input: Test folder containing many test case results as calculated by **App6_BulkTestExecutor**. 
Output: On the console the averaging and data analysis of these results are shown.


# 3. Mode of Use
- In order to run simulations we must first test cases. A test case requires the following data to be set:
	- The map
	- The partitions
	- Location of the agents
	- Locations of the tasks
- A single test case can be created by using the following apps in order:
	1. Use **App1_MapDrawer** to save the map file.
	2. Using **App2B_DrawPartitions** import the map file and draw the partitions, export the partitioned map file.
	3. Using **App3_AgentPlacer** import a partitioned map file, place the home and guest agents into the partitioned map file, export the map with agents file.
	4. Using **App4_TaskGenerator** import a map with agents file, input the task count for each team and click generate, afterwards you can export the completed test case which can be used in the simulator named **Simulate**
- Alternatively you can create many test cases at once using **App5_BulkTestGenerator**.
	1. Use **App1_MapDrawer** to save the map file.
	2. Using **App2B_DrawPartitions** import the map file and draw the partitions, export the partitioned map file.
	3. Run **App5_BulkTestGenerator**, this app runs in the console. At opening you will have to select the partitioned map file you want to create many test cases out of.
	4. Follow the instructions in the console to select the number of agents for each team, number of tasks per agent and the number of test cases you would like to create. The test cases will be created in ./tests/map_name/tests Also a setting file will be created in ./tests/map_name/ which can be used later on to create more test cases that use the same agent placement and possible task endpoints.
- After creating a test case this test case can be run using **Simulate** or **App6_BulkTestExecutor**. **Simulate** offers a GUI and detailed console reports, **App6_BulkTestExecutor** offers the same software but with multithreading and no console reporting. So it is best practice to first make sure an algorithm works correctly using **Simulate** on a select set of small test cases, then create many test cases using **App5_BulkTestGenerator** and test all these test cases using **App6_BulkTestExecutor**. **Simulate** showcases the simulation results at the end while **App6_BulkTestExecutor** saves the simulation results under ./results/map_name for each test case. The average results and the analysis of these bulk test results can be reported by using **App7_AnalysisofResults**
- **Simulate_combined_team** and **App6_BulkTestExecutor_Combined** exist to handle the case where we consider the two teams acting as one (No need for observations to know other teams' agents' locations.)
