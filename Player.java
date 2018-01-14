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

    private static Direction getRandom(Direction[] array) {
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
                    System.out.println(factory.health());
                    
                    if ( gc.canBuild( r.id(), factory.id() ) ){ // WOULD SAY TRUE, THEN BUILD WOULDN'T INCREASE THE HEALTH
                        System.out.println("\tBUILDING");
                        gc.build( r.id(), factory.id() );
                    }
                    
                    gc.nextTurn();
                }

                System.out.println("\n FACTORY AT FULL HEALTH \n");
            }
        }

        while(true){
            System.out.println("\n");
            System.out.println(gc.round());
            for(int u =0; u< gc.myUnits().size(); u++){
                if( gc.myUnits().get(u).unitType() == UnitType.Factory ){
                    System.out.println("\tFactory");
                    factory = gc.myUnits().get(u);
                    if( gc.canProduceRobot( factory.id(), UnitType.Knight ) ){
                        gc.produceRobot( factory.id(), UnitType.Knight);

                        System.out.println("\t\t Created Knight");
                    }
                    if( factory.structureGarrison().size() > 0){
                        Direction dir = getRandom(directions);
                        if( gc.canUnload(factory.id(), dir) ){
                            gc.unload(factory.id(), dir);

                            System.out.println("\t\t\t Deployed knight");
                        }
                    }
                }
                if( gc.myUnits().get(u).unitType() == UnitType.Knight ){
                    Team op;
                    if (gc.team()==Team.Red){
                        op=Team.Blue;
                    }
                    else{
                        op=Team.Red;
                    }
                    nearby = gc.senseNearbyUnitsByTeam(gc.myUnits().get(u).location().mapLocation() ,50,op);
                    if (gc.canAttack(gc.myUnits().get(u).id(),nearby.get(0).id())){
                        gc.attack(gc.myUnits().get(u).id(),nearby.get(0).id());
                    }
                    else{
                        Direction dir = gc.myUnits().get(u).location().mapLocation().directionTo(nearby.get(0).location().mapLocation());
                        if ( gc.canMove(gc.myUnits().get(u).id(),dir)){
                            gc.moveRobot(gc.myUnits().get(u).id(),dir);
                        }
                    }
                }
            }
            System.out.println("\n");
            
        }
    }
}
