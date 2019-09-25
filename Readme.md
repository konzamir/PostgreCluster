## Task

PostgreSQL DB Cluster хранилище данных представлено в виде отказоустойчивого кластера с механизмами failover и streaming replication. Все узлы кластера отдают данные в режиме READ, только Master работает в режиме WRITE. При отказе Master, одна из Slave реплик переключается в режим Master.
