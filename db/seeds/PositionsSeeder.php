<?php

require_once __DIR__ . '/BaseSeeder.php';

class PositionsSeeder extends BaseSeeder
{
    /**
     * Run Method.
     *
     * Write your database seeder using this method.
     *
     * More information on writing seeders is available here:
     * https://book.cakephp.org/phinx/0/en/seeding.html
     */
    public function run(): void
    {
        require_once __DIR__ . '/../../src/common/libs/Auth/serverActions.php';
        $positionGroups = [
            [
                "positionsGroups_id" => 1,
                "positionsGroups_name" => "Administrator",
                "positionsGroups_actions" => implode(",", array_keys($serverActions))
            ]
        ];

        $positions = [
            [
                "positions_id" => 1,
                "positions_displayName" => "Super-admin",
                "positions_positionsGroups" => "1",
                "positions_rank" => 1
            ]
        ];

        $this->upsert('positionsGroups', $positionGroups, ['positionsGroups_id']);
        $this->upsert('positions', $positions, ['positions_id']);
    }
}
