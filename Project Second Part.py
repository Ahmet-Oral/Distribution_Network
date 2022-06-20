import pandas as pd
import gurobipy as gp
from gurobipy import GRB

# Creating dictionaries for factory production, road output limits, and warehouse demand.

# Amount of units produced
F1_Supply = dict({'F1': 50})
F2_Supply = dict({'F2': 40})

# Road capacity
DC_W2_Capacity = dict({'DC': 80})
F1_F2_Capacity = dict({'F1': 10})

# Warehouse needs
W1_Demand = dict({'W1': 30})
W2_Demand = dict({'W2': 60})

# Possible paths and transportation cost (per unit)
arcs, cost, road_Cost = gp.multidict({
    ('F1', 'DC'): [400, 1000],
    ('F1', 'F2'): [200, 1000],
    ('F1', 'W1'): [900, 1000],
    ('F2', 'DC'): [300, 1000],
    ('DC', 'W2'): [100, 1000],
    ('W1', 'W2'): [300, 1000],
    ('W2', 'W1'): [200, 1000]})

# Creating our model
model = gp.Model('Ahmet_Mehlika_Beyza')

# Creating flow of units (possible paths)
flow = model.addVars(arcs, name="flow")

#Defining our objectives by hand, I did this because when I used for loops and iterate over gp.quicksum methods I had
#... syntax errors that I couldn't fix
#There are 2 objectives, for normal road cost, and road build cost
obj1 = ((gp.quicksum(flow.select('F1', 'DC')) * cost['F1', 'DC'])
                    + (gp.quicksum(flow.select('F1', 'W1')) * cost['F1', 'W1'])
                    + (gp.quicksum(flow.select('F1', 'F2')) * cost['F1', 'F2'])
                    + (gp.quicksum(flow.select('F2', 'DC')) * cost['F2', 'DC'])
                    + (gp.quicksum(flow.select('DC', 'W2')) * cost['DC', 'W2'])
                    + (gp.quicksum(flow.select('W1', 'W2')) * cost['W1', 'W2'])
                    + (gp.quicksum(flow.select('W2', 'W1')) * cost['W2', 'W1'])

                    )

obj2 = ((gp.quicksum(flow.select('F1', 'DC')) * road_Cost['F1', 'DC'])
                    + (gp.quicksum(flow.select('F1', 'W1')) * road_Cost['F1', 'W1'])
                    + (gp.quicksum(flow.select('F1', 'F2')) * road_Cost['F1', 'F2'])
                    + (gp.quicksum(flow.select('F2', 'DC')) * road_Cost['F2', 'DC'])
                    + (gp.quicksum(flow.select('DC', 'W2')) * road_Cost['DC', 'W2'])
                    + (gp.quicksum(flow.select('W1', 'W2')) * road_Cost['W1', 'W2'])
                    + (gp.quicksum(flow.select('W2', 'W1')) * road_Cost['W2', 'W1']))

#Defining our objective in our model with priorities
model.setObjectiveN(obj1, 0, 2)
model.setObjectiveN(obj2, 1, 2)


# Creating and adding constraints to our model
# F1 Supply amount
supplyF1 = model.addConstr((gp.quicksum(flow.select('F1', '*'))
                            <= F1_Supply['F1']), name="supplyF1")

# F2 Supply amount
supplyF2 = model.addConstr((gp.quicksum(flow.select('F2', '*')) <=
                            (F2_Supply['F2'] + gp.quicksum(flow.select('F1', '*')) - gp.quicksum(
                                flow.select('F1', 'W1')) - gp.quicksum(flow.select('F1', 'DC')))), name="supplyF2")

# F1 to F2 capacity
capacityF1_F2 = model.addConstr((gp.quicksum(flow.select('F1', 'F2'))
                                 <= F1_F2_Capacity['F1']), name="capacityF1_F2")

# DC to W2 capacity
capacityDC_W2 = model.addConstr((gp.quicksum(flow.select('*', 'DC'))
                                 <= DC_W2_Capacity['DC']), name="capacityDC_W2")

# DC flow conservation
DC_flow_conservation = model.addConstr((gp.quicksum(flow.select('DC', '*'))
                                        == gp.quicksum(flow.select('*', 'DC'))), name="DC_flow_conservation")

# W1 flow conservation
W1_flow_conservation = model.addConstr((gp.quicksum(flow.select('W2', '*'))
                                        <= gp.quicksum(flow.select('*', 'W2'))), name="W1_flow_conservation")

# W2 flow conservation
W2_flow_conservation = model.addConstr((gp.quicksum(flow.select('W2', '*'))
                                        <= gp.quicksum(flow.select('*', 'W2'))), name="W2_flow_conservation")

# W1 needs
W1_needs = model.addConstr((gp.quicksum(flow.select('*', 'W1'))
                            == W1_Demand['W1'] + gp.quicksum(flow.select('W1', '*'))),
                           name="W1_needs")

# W2_needs
W2_needs = model.addConstr((gp.quicksum(flow.select('*', 'W2'))
                            == W2_Demand['W2'] + gp.quicksum(flow.select('W2', '*'))),
                           name="W2_needs")
model.write("secondModel.lp")
model.optimize()

# Creating a dataFrame to visualize transported units
product_flow = pd.DataFrame(columns=["From  ", "To", " Flow   ", "CostPerUnit ", "RoadCost", "TotalCost"])

# Iterating over possible paths and adding values to the dataFrame
for arc in arcs:  # arc is a possible path such as F1->F2 -- F1->W1.....
    if flow[arc].x > 0:  # If that path has been used
        # Adding used paths, amount of unit flow and cost of that path to the dataFrame
        product_flow = product_flow.append({"From  ": arc[0] + "  ->",
                                            "To": arc[1],
                                            " Flow   ": str(int(flow[arc].x)) + "   ",
                                            "CostPerUnit ": str((arcs, cost[arc])[1]) + "$   ",
                                            "RoadCost": str((arcs, road_Cost[arc])[1]) + "$  ",
                                            "TotalCost": str(int(((arcs, cost[arc])[1] * flow[arc].x + (arcs, road_Cost[arc])[1]))) + "$"},
                                           ignore_index=True)
product_flow.index = [''] * len(product_flow)  # Removing dataFrame indexes for aesthetic look

print("--------------------------------------------------------------------------\n\n")
print(product_flow)

print("--------------------------------------------")

# Calculating road cost
rCost = 0
for arc in arcs:
    if flow[arc].x > 0:
        #rCost += int(flow[arc].x * (arcs, road_Cost[arc])[1]) - (arcs, road_Cost[arc])[1]
        rCost += (arcs, road_Cost[arc])[1]

obj = model.getObjective()
print("Sum of Total Cost:", int(obj.getValue())+rCost, "$")
