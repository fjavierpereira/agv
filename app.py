
import streamlit as st
import time
import matplotlib.pyplot as plt

class AGV:
    def __init__(self, agv_id, speed):
        self.agv_id = agv_id
        self.speed = speed
        self.available = True
        self.task_end_time = 0
        self.task = None

class Station:
    def __init__(self, name, takt_time):
        self.name = name
        self.takt_time = takt_time
        self.queue = []
        self.busy_until = 0

class CircuitSimulator:
    def __init__(self, stations, agvs, total_time, distance_matrix):
        self.stations = {s.name: s for s in stations}
        self.agvs = {a.agv_id: a for a in agvs}
        self.total_time = total_time
        self.distance_matrix = distance_matrix
        self.time = 0
        self.log = []
        self.running = False

    def simulate_step(self):
        if self.time >= self.total_time:
            return False
        for agv in self.agvs.values():
            if not agv.available and self.time >= agv.task_end_time:
                agv.available = True
                self.log.append((self.time, f"AGV {agv.agv_id} completed task at {agv.task}"))
                agv.task = None
        for station in self.stations.values():
            if station.queue and self.time >= station.busy_until:
                station.queue.pop(0)
                station.busy_until = self.time + station.takt_time
                self.log.append((self.time, f"Station {station.name} processed a unit"))
        self.time += 1
        return True

    def assign_task(self, agv_id, station_name):
        agv = self.agvs.get(agv_id)
        station = self.stations.get(station_name)
        if agv and station and agv.available:
            travel_time = self.distance_matrix.get(("charging", station_name), 20) / agv.speed
            task_duration = travel_time + station.takt_time
            agv.task_end_time = self.time + task_duration
            agv.available = False
            agv.task = station_name
            station.queue.append(agv)
            self.log.append((self.time, f"AGV {agv.agv_id} assigned to {station.name}, ETA {task_duration:.1f}s"))

    def reset(self):
        self.time = 0
        self.log = []
        for agv in self.agvs.values():
            agv.available = True
            agv.task = None
            agv.task_end_time = 0
        for station in self.stations.values():
            station.queue.clear()
            station.busy_until = 0

    def report_plot(self):
        times, _ = zip(*self.log) if self.log else ([], [])
        plt.figure(figsize=(8, 3))
        plt.hist(times, bins=50)
        plt.title("Event Distribution Over Time")
        plt.xlabel("Time (s)")
        plt.ylabel("Number of Events")
        st.pyplot(plt)

# Inicialización
if 'sim' not in st.session_state:
    stations = [Station("A", 30), Station("B", 45), Station("C", 60)]
    agvs = [AGV(1, 1.5), AGV(2, 1.0), AGV(3, 2.0)]
    distance_matrix = {
        ("charging", "A"): 30,
        ("charging", "B"): 40,
        ("charging", "C"): 50,
    }
    st.session_state.sim = CircuitSimulator(stations, agvs, 3600, distance_matrix)
    st.session_state.running = False

sim = st.session_state.sim

# Interfaz
st.title("Simulador de AGVs")

col1, col2, col3 = st.columns(3)
with col1:
    agv_id = st.selectbox("Selecciona AGV", options=[1, 2, 3])
with col2:
    station = st.selectbox("Selecciona estación", options=list(sim.stations.keys()))
with col3:
    if st.button("Asignar tarea"):
        sim.assign_task(agv_id, station)

st.write(f"Tiempo actual: {sim.time}s")
if st.button("Play / Avanzar 1 paso"):
    sim.simulate_step()

if st.button("Pausar"):
    st.session_state.running = False

if st.button("Reiniciar simulación"):
    sim.reset()

if st.button("Ver reporte" and sim.log):
    sim.report_plot()

st.subheader("Estado de AGVs")
for agv in sim.agvs.values():
    estado = "Libre" if agv.available else f"Ocupado hasta {agv.task_end_time}s (en {agv.task})"
    st.text(f"AGV {agv.agv_id}: {estado}")

st.subheader("Estado de estaciones")
for s in sim.stations.values():
    st.text(f"Estación {s.name}: {len(s.queue)} en cola, ocupada hasta {s.busy_until}s")
