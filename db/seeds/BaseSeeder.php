<?php

declare(strict_types=1);

use Phinx\Seed\AbstractSeed;

abstract class BaseSeeder extends AbstractSeed
{
    /**
     * Insert or update rows by primary or unique keys.
     *
     * @param array<int, array<string, mixed>> $rows
     * @param array<int, string> $uniqueColumns
     */
    protected function upsert(string $table, array $rows, array $uniqueColumns, int $chunkSize = 100): void
    {
        if ($rows === [] || $chunkSize < 1) {
            return;
        }

        $columns = array_keys(reset($rows));
        $updateColumns = array_values(array_diff($columns, $uniqueColumns));
        if ($updateColumns === []) {
            $updateColumns = $columns;
        }

        $connection = $this->getAdapter()->getConnection();

        foreach (array_chunk($rows, $chunkSize) as $chunk) {
            $placeholders = '(' . implode(',', array_fill(0, count($columns), '?')) . ')';
            $valuesClause = implode(',', array_fill(0, count($chunk), $placeholders));

            $updates = implode(', ', array_map(static function (string $column): string {
                return sprintf('`%s` = VALUES(`%s`)', $column, $column);
            }, $updateColumns));

            $sql = sprintf(
                'INSERT INTO `%s` (%s) VALUES %s ON DUPLICATE KEY UPDATE %s',
                $table,
                implode(', ', array_map(static function (string $column): string {
                    return sprintf('`%s`', $column);
                }, $columns)),
                $valuesClause,
                $updates
            );

            $statement = $connection->prepare($sql);
            $values = [];
            foreach ($chunk as $row) {
                foreach ($columns as $column) {
                    $values[] = $row[$column] ?? null;
                }
            }

            $statement->execute($values);
        }
    }

    /**
     * Determine if a row exists for the supplied conditions.
     */
    protected function recordExists(string $table, array $conditions): bool
    {
        if ($conditions === []) {
            return false;
        }

        $clauses = [];
        $values = [];

        foreach ($conditions as $column => $value) {
            $clauses[] = sprintf('`%s` = ?', $column);
            $values[] = $value;
        }

        $sql = sprintf(
            'SELECT 1 FROM `%s` WHERE %s LIMIT 1',
            $table,
            implode(' AND ', $clauses)
        );

        $statement = $this->getAdapter()->getConnection()->prepare($sql);
        $statement->execute($values);

        return (bool) $statement->fetchColumn();
    }
}
