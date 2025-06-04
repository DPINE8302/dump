setTimeout(() => {
    if (!sim.visualCleanupScheduled) { // Check flag
        sim.visualLayers.forEach(layer => { if (map.hasLayer(layer)) map.removeLayer(layer); });
        sim.visualLayers = [];
        if (map.hasLayer(sim.epicenterMarker)) map.removeLayer(sim.epicenterMarker);
        sim.visualCleanupScheduled = true; // Set flag
    }
}, SIMULATION_VISUAL_LIFESPAN_MS);