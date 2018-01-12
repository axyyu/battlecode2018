// import the API.
// See xxx for the javadocs.
import bc.*;
import java.util.*;

public class Player {

    public static void main(String[] args) {
        // Connect to the manager, starting the game
        GameController gc = new GameController();

        // Map setup
        // earthMap = gc.starting_map(Planet.Earth);
        // marsMap = gc.starting_map(Planet.Mars);

        // Initial Setup
        /*
        while (true) {
            units = gc.myUnits();
            karbonite = gc.karbonite();

            manageUpgrades();

            if( gc.planet() == Planet.Earth ){
                earth();
            }
            else{
                mars();
            }

            // Submit the actions we've done, and wait for our next turn.
            gc.nextTurn();
        }
        */
        if( gc.planet() == Planet.Earth ){
            test(gc);
        }
        else{
            System.out.println("\t lol its mars");
            while(true){
                gc.nextTurn();
            }
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
    private static void manageUpgrades(GameController gc){
        gc.researchInfo();
        gc.queueResearch(UnitType.Worker);
    }

    /*
     * Code for Earth
     */
    private static void earth(GameController gc){
        
    }

    /*
     * Code for Mars
     */
    private static void mars(GameController gc){
        
    }

    private static Direction getRandom(Directions[] array) {
        int rnd = new Random().nextInt(array.length);
        return array[rnd];
    }

    private static void test(GameController gc){
        Direction[] directions = Direction.values();

        System.out.println("\nTEST\n");

        Unit r = gc.myUnits().get(0);

        if ( gc.canBlueprint( r.id(), UnitType.Factory, Direction.South ) ){
            gc.blueprint( r.id(), UnitType.Factory, Direction.South );
        }

        gc.nextTurn();

        System.out.println("\nCREATED BLUEPRINT\n");

        VecUnit nearby = gc.senseNearbyUnits( r.location().mapLocation() , 2 );
        Unit factory;

        for( int ai = 0; ai < nearby.size(); ai++ ){
            System.out.println("\nFOUND BLUEPRINT\n");

            Unit a = nearby.get(ai);
            if ( a.unitType() == UnitType.Factory ){
                factory = a;
                while ( factory.health() != factory.maxHealth() ){
                    if ( gc.canBuild( r.id(), factory.id() ) ){
                        gc.build( r.id(), factory.id() );
                    }
                    gc.nextTurn();
                }
            }
        }

        while(true){

            for(int u =0; u< gc.myUnits().size(); u++){
                if( gc.myUnits().get(u).unitType() == UnitType.Factory ){
                    factory = gc.myUnits().get(u);
                    if( gc.canProduceRobot( factory.id(), UnitType.Knight ) ){
                        gc.produceRobot( factory.id(), UnitType.Knight);
                    }
                    if( factory.structureGarrison().size() > 0){
                        Direction dir = getRandom(directions);
                        if( gc.can_unload(factory.id(), dir) ){
                            gc.unload(factory.id(), dir);
                        }
                    }
                }
                if( gc.myUnits().get(u).unitType() == UnitType.Knight ){
                    VecUnit nearby = gc.senseNearbyUnits( gc.myUnits().get(u).location().mapLocation() , 2 );
                }
            }
            
        }

        while (true) {
            gc.nextTurn();
        }
    }
}
