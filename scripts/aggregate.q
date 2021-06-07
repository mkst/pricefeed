// combine provider books into a single pool

emptySchema: flip `date`sym`time`bidtime`bidpx`bidqty`bidlp`asktime`askpx`askqty`asklp!"dsp********"$\:()

readProviders:{[configFile]
    providers:("issb";enlist csv) 0: configFile;
    :exec distinct name from providers where aggregate;
    };

getPriceAtIndexes:{[poolTime;tabs;indexes]
    // pull out prices from each table
    bids:flip `bidtime`bidpx`bidqty`bidlp#tmp:raze each flip tabs@'indexes;
    asks:flip `asktime`askpx`askqty`asklp#tmp;
    // sort bids descending
    bids:`bidpx xdesc `bidtime`bidqty xasc bids;
    // sort asks ascending
    asks:`askpx xasc `asktime`askqty xasc asks;
    // combine into single entry
    bids:select bidtime, bidpx, bidqty, bidlp by time from update time:poolTime from bids;
    asks:select asktime, askpx, askqty, asklp by time from update time:poolTime from asks;
    // join and return
    :0!bids uj asks;
    };

getPriceAtIndexesWrapper:{[row;tableNames]
    getPriceAtIndexes[row`time;tableNames;row tableNames]
    };

unenum:{ update value sym, value each bidlp, value each asklp from x };

loadData:{[hdbDir;dt;table;provider]
    // load up HDB
    system "l ",1 _ string .Q.dd[hdbDir;provider];
    // select from table where date = dt
    data:.[{[tab;d] unenum ?[tab;enlist (=;`date;d);0b;()] };(table;dt);emptySchema];
    // save in global space
    provider set data
    };

createLookupTableForDate:{[dt;providers]
    // select time, tab:i from tab
    indexes:{[tab] ?[tab;();0b;(`time;tab)!`time`i] } each providers;
    // combine tables
    lookupTable:`time xasc (uj/) indexes;
    // fill forward
    lookupTable:fills lookupTable;
    // take latest
    lookupTable:0!select by time from lookupTable;
    // return lookupTable
    :lookupTable;
    };

createPool:{[lookupTable;providers]
    pool:raze getPriceAtIndexesWrapper[;providers] peach lookupTable;
    // return () if no prices
    :$[count pool;`time xasc pool;()];
    };

main:{[options]
    // options
    opts:.Q.opt options;
    if[not all `date`hdbDir`table`providers in key opts;
        -1"ERROR: -date, -hdbDir, -table and -providers are all required arguments";
        exit 1;
        ];
    // parse options
    dt:"D"$first opts`date;
    hdbDir:hsym `$first opts`hdbDir;
    table:`$first opts`table;
    providersConfig:hsym `$first opts`providers;
    // parse provider config
    providers:readProviders providersConfig;
    // load each provider hdb table into memory
    loadData[hdbDir;dt;table] each providers;
    // merge indexes for each provider
    lookupTable:createLookupTableForDate[dt;providers];
    // pull symbol out of book name
    symbol:`$ssr[string table;"book";""];
    // set name of table to save down
    tableName:`$"pool",string symbol;
    // pull out books and combine
    pool:createPool[lookupTable;providers];
    if[not count pool;
        -1"Nothing to do for ",(.Q.s1 (dt;symbol)), ". Exiting";
        exit 0;
        ];
    -1"Aggregated ",(string count pool)," prices for ",.Q.s1 (dt;symbol);
    // add sym column
    pool:`time`sym xcols update sym:symbol from pool;
    // set table in global space
    tableName set pool;
    // set compression
    .z.zd:17 2 6;
    // write down pool
    .Q.dpft[.Q.dd[hdbDir;`agg];dt;`sym;] tableName
    };

if[`aggregate.q = `$last "/" vs string .z.f; main .z.x; exit 0];
