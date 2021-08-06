// convert pool into bbo with rudimentary book uncrossing

getFilteredIndexes:{[bidPx;askPx]
    bidIdx: til count bidPx;  // indices of bids to keep
    askIdx: til count askPx;  // indices of asks to keep

    while[(bid > ask) and (not null bid: first bids:bidPx bidIdx) and (not null ask: first asks:askPx askIdx);
        // remove biggest difference between price levels
        bidDiff: bids[0] - bids[1];
        askDiff: asks[1] - asks[0];
        $[bidDiff > askDiff;
            bidIdx: 1 _ bidIdx;
            askIdx: 1 _ askIdx
            ];
    ];
    // return as dictionary
    :`bidIdx`askIdx!(bidIdx;askIdx);
    };

createBBO:{[priceData]
    // enforce type
    table: update "f"$bidpx, "f"$askpx from priceData;
    // remove nulls
    table: select from table where not null bidpx[;0], not null askpx[;0];
    // unenumerate
    table: update value sym from table;
    // identify crossed
    crossed: select from table where bidpx[;0] > askpx[;0];
    // remove crossed from original table
    table: select from table where bidpx[;0] <= askpx[;0];
    // create bbo table
    bbo: select time, sym, bid:first each bidpx, ask:first each askpx from table;

    // filter crossed to rows with at least 2 prices on both sides
    crossed: select from crossed where 1 < count each bidpx, 1 < count each askpx;
    // add indexes to produce uncrossed book
    crossed: update uncrossed_idx:getFilteredIndexes'[bidpx;askpx] from crossed;
    // apply indexes
    crossed: update bidpx:bidpx@'uncrossed_idx[;`bidIdx], askpx:askpx@'uncrossed_idx[;`askIdx] from crossed;
    // remove null rows
    crossed: select from crossed where not null bidpx[;0], not null askpx[;0];
    // create bbo2 from newly uncrossed rows
    bbo2: select time, sym, bid:first each bidpx, ask:first each askpx from crossed;
    // sort and return
    :`time xasc bbo,bbo2;
    };

main:{[options]
    opts:.Q.opt options;
    if[not all `date`hdbDir`outDir`table in key opts;
        -1"ERROR: -date, -hdbDir, -outDir and -table are required arguments";
        exit 1;
        ];
    // parse options
    dt:"D"$first opts`date;
    hdbDir:hsym `$first opts`hdbDir;
    table:`$first opts`table;
    outDir:hsym `$first opts`outDir;
    // pull symbol out of pool name
    symbol:`$ssr[string table;"pool";""];
    tableName:`$"bbo",string symbol;
    // load HDB
    system "l ",(1 _ string hdbDir),"/agg";
    // create bbo
    bbo:createBBO[select from table where date=dt];
    if[not count bbo;
        -1"Nothing to do for",(.Q.s1 (dt;symbol)),". Exiting";
        exit 0;
        ];
    -1 (string .z.p)," BBO contains ",(string count bbo)," prices for ",.Q.s1 (dt;symbol);
    // writedown csv
    .Q.dd[outDir;` sv (symbol;`csv)] 0: csv 0: bbo;

    if[`writeHdb in key opts;
        // set table in global space
        tableName set bbo;
        // set compression
        .z.zd: 17 2 6;
        // write down bbo
        .Q.dpft[.Q.dd[hdbDir;`bbo];dt;`sym;] tableName;
        ];
    };

if[`bbo.q = `$last "/" vs string .z.f; main .z.x; exit 0];
