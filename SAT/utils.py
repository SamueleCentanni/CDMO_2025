
def print_weekly_schedule(match_list, num_teams):
    '''
    Stampa lo schedule settimana per settimana, con periodi e partite,
    indicando chi gioca in casa e chi fuori.

    match_list: lista di tuple (indice_squadra_home, indice_squadra_away, indice_settimana, indice_periodo)
                (assumendo indici 0-based, per la stampa saranno convertiti a 1-based)
    num_teams: numero di squadre
    '''
    num_weeks = num_teams - 1
    num_periods = num_teams // 2

    print("\n--- SCHEDULE DEL TORNEO ---")
    print(f"Numero di squadre: {num_teams}")
    print(f"Numero di settimane: {num_weeks}")
    print(f"Periodi per settimana: {num_periods}")
    print("---------------------------\n")

    # Costruisci dizionario per accesso rapido: (settimana_0based, periodo_0based) → (squadra_home_0based, squadra_away_0based)
    schedule = {}
    for i, j, w, p in match_list:
        # Assicurati che gli indici siano 0-based per il dizionario
        schedule[(w - 1, p - 1)] = (i - 1, j - 1) # Converti da 1-based a 0-based se match_list è 1-based

    for w_idx in range(num_weeks):
        print(f"Settimana {w_idx + 1}:")
        for p_idx in range(num_periods):
            # Cerca la partita per la settimana e il periodo 0-based
            match = schedule.get((w_idx, p_idx))
            if match:
                home_team_idx, away_team_idx = match
                # Stampa con indici 1-based per l'utente
                print(f"  Periodo {p_idx + 1}: Squadra {home_team_idx + 1} (Casa) vs Squadra {away_team_idx + 1} (Trasferta)")
            else:
                # Questo caso non dovrebbe verificarsi se la soluzione è valida
                print(f"  Periodo {p_idx + 1}: [NESSUNA PARTITA PROGRAMMATA]")
        print() # Linea vuota tra le settimane per maggiore leggibilità

    print("--- FINE SCHEDULE ---\n")