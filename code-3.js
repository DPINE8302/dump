if (now - sim.lastImpactCalcTime > IMPACT_CALCULATION_INTERVAL_MS) {
    processImpactsForSimulation(sim);
    sim.lastImpactCalcTime = now;
    // ... (update UI for latest event) ...
}