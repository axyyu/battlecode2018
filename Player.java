// import the API.
// See xxx for the javadocs.
import bc.*;

public class Player {

    // Maps
    private static PlanetMap earthMap;
    private static PlanetMap marsMap;

    // Unit
    private static VecUnit units;

    // Economy
    private static long karbonite;

    public static void main(String[] args) {
        // Connect to the manager, starting the game
        GameController gc = new GameController();

        // Map setup
        earthMap = gc.starting_map(Planet.Earth);
        marsMap = gc.starting_map(Planet.Mars);

        // Initial Setup
        while (true) {
            units = gc.myUnits();
            karbonite = gc.karbonite();

            manageUpdates();

            if( gc.planet() == Planet.Earth ){
                earth();
            }
            else{
                mars();
            }

            // Submit the actions we've done, and wait for our next turn.
            gc.nextTurn();
        }
    }

    /*
     * Manage Upgrades
     *
     * Upgrade Order:
     *  Worker - Karbonite
     *
     *  Rocket - Rocketry
     */
    private static void manageUpgrades(){
        gc.researchInfo();
        gc.queueResearch(UnitType.Worker);
    }

    /*
     * Code for Earth
     */
    private static void earth(){
        
    }

    /*
     * Code for Mars
     */
    private static void mars(){
        
    }
}
