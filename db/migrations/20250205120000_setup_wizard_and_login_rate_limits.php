<?php

use Phinx\Db\Adapter\MysqlAdapter;
use Phinx\Migration\AbstractMigration;

class SetupWizardAndLoginRateLimits extends AbstractMigration
{
    public function change(): void
    {
        if (!$this->hasTable('loginRateLimits')) {
            $this->table('loginRateLimits', [
                'id' => false,
                'primary_key' => ['loginRateLimits_id'],
                'engine' => 'InnoDB',
                'encoding' => 'utf8mb4',
                'collation' => 'utf8mb4_unicode_ci',
                'comment' => 'Track login attempts for rate limiting',
                'row_format' => 'DYNAMIC',
            ])
                ->addColumn('loginRateLimits_id', 'integer', [
                    'null' => false,
                    'limit' => MysqlAdapter::INT_REGULAR,
                    'identity' => 'enable',
                ])
                ->addColumn('loginRateLimits_type', 'string', [
                    'null' => false,
                    'limit' => 32,
                    'after' => 'loginRateLimits_id',
                ])
                ->addColumn('loginRateLimits_key', 'string', [
                    'null' => false,
                    'limit' => 128,
                    'after' => 'loginRateLimits_type',
                ])
                ->addColumn('loginRateLimits_attempts', 'integer', [
                    'null' => false,
                    'default' => 0,
                    'limit' => MysqlAdapter::INT_SMALL,
                    'after' => 'loginRateLimits_key',
                ])
                ->addColumn('loginRateLimits_lastAttempt', 'datetime', [
                    'null' => true,
                    'after' => 'loginRateLimits_attempts',
                ])
                ->addColumn('loginRateLimits_blockedUntil', 'datetime', [
                    'null' => true,
                    'after' => 'loginRateLimits_lastAttempt',
                ])
                ->addIndex(['loginRateLimits_type', 'loginRateLimits_key'], [
                    'name' => 'loginRateLimits_type_key_unique',
                    'unique' => true,
                ])
                ->create();
        }

        $configExists = $this->fetchRow("SELECT 1 FROM config WHERE config_key = 'SETUP_COMPLETED' LIMIT 1");
        if ($configExists === false) {
            $this->table('config')->insert([
                'config_key' => 'SETUP_COMPLETED',
                'config_value' => '0',
            ])->saveData();
        }
    }
}
