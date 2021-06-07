// convert h5 dumped out CSV into KDB database

unix2ts:-10957D+"p"$1000*

// bid provider, bid px, bid qty, bid time, .. asks..., time
createSchema:{[cnt] raze (cnt#"s";cnt#"f";cnt#"f";cnt#"j";cnt#"s";cnt#"f";cnt#"f";cnt#"j";1#"j") };

columnNames:{[col;cnt] `$raze each string[col],/:string til cnt };
queryHelper:{[col] (,;first col;$[2<count col;.z.s 1 _ col;last col]) };

queryBuilder:{[cnt]
    :`time`bidtime`bidpx`bidqty`bidlp`asktime`askpx`askqty`asklp!(
        (first;`time);
        queryHelper columnNames[`bid_time;cnt];
        queryHelper columnNames[`bid_px;cnt];
        queryHelper columnNames[`bid_size;cnt];
        queryHelper columnNames[`bid_provider;cnt];
        queryHelper columnNames[`ask_time;cnt];
        queryHelper columnNames[`ask_px;cnt];
        queryHelper columnNames[`ask_size;cnt];
        queryHelper columnNames[`ask_provider;cnt])
    };

loadCsv:{[filename;columnCount]
    // load csv from disk
    book:(createSchema[columnCount];enlist csv) 0: filename;
    // functional select
    book:?[book;();enlist[`x]!enlist `i;queryBuilder columnCount];
    // collect garbage from csv import
    .Q.gc[];
    // time will never be zero unless there is no update at that level
    book:update bid_cnt:{sum not 0 = x} each bidtime, ask_cnt:{sum not 0 = x} each asktime from book;
    // reduce column lengths to used lengths
    book:select time,
        bid_cnt#'bidtime, bid_cnt#'bidpx, bid_cnt#'bidqty, bid_cnt#'bidlp,
        ask_cnt#'asktime, ask_cnt#'askpx, ask_cnt#'askqty, ask_cnt#'asklp from book;
    // map providers
    book:update providersMap each bidlp, providersMap each asklp from book;
    // convert ms since epoch to Timestamp
    book:update unix2ts time, unix2ts bidtime, unix2ts asktime from book;
    // reorder columns
    :`time`bidtime`bidpx`bidqty`bidlp`asktime`askpx`askqty`asklp xcols book;
    };

loadProviders:{[filename]
    // id,name,alias
    tmp:("*ss";enlist csv) 0: filename;
    // provider is a byte object coming from Python so map the provider id to match
    tmp:update id:{ `$"b'",x,"'" } each id from tmp;
    // return dictionary
    exec id!alias from tmp
    };

main:{[options]
    opts:.Q.opt options;
    if[not all `date`infile`outpath`providers in key opts;
        -1" -date, -infile and -outpath -providers are all required arguments";
        exit 1
        ];
    dt:"D"$first opts`date;
    infile:hsym `$first opts`infile;
    if[()~key infile;
        -1"ERROR: infile does not exist";
        exit 2
        ];
    outpath:hsym `$first opts`outpath;
    // default column count to 10
    columnCount:$[`columns in key opts;"J"$first opts`columns;10];
    // load in provider map
    providersMap::loadProviders hsym `$first opts`providers;
    // process csv
    book:loadCsv[infile;columnCount];
    // take table name from filename
    tableName:`$first "." vs last "/" vs first opts`infile;
    // take symbol from filename if -symbol not specified
    symbol:`$$[`symbol in key opts;
        first opts`symbol;
        ssr[string tableName;"book";""]];
    // add sym column and reorder
    book:`time`sym xcols update sym:symbol from book;
    // set table in global space
    tableName set book;
    // set compression
    .z.zd: 17 2 6;
    // writedown
    .Q.dpft[outpath;dt;`sym;] tableName
    };

if[`csv2q.q = `$last "/" vs string .z.f; main .z.x; exit 0];
