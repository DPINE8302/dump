setTimeout(() => {
    if (!sim.visualCleanupScheduled) { /* ... ensure visual cleanup ... */ }
    activeSimulations = activeSimulations.filter(s => s.id !== sim.id);
    updateGlobalCityImpactList(); 
}, Math.max(0, SIMULATION_VISUAL_LIFESPAN_MS - elapsedMs) + 1000);