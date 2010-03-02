source("functions.r");


available_nodes <- function (ns, from, to, type, fmt="%b")
{
    # find 'type' range of days
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, fmt)
    hbreaks<-unclass(as.POSIXct(dates))

    xx<-NULL;
    yy<-NULL;

    for ( i in seq(1,length(hbreaks)-1) )
    {
        # get range from ns
        ns_sub <- ns[which(ns$date > hbreaks[i] & ns$date <= hbreaks[i+1] & ns$status == 'BOOT'),]
        nodes <- length(ns_sub$date)

        xx<- c(xx, hbreaks[i])
        yy<- c(yy, nodes)

    }
    m<- months[1:length(months)-1]
    return (rbind(xx,yy,m))
}



open_tickets <- function (t, from, to, type, fmt="%b")
{
    # find 'type' range of days
    dates <-seq(as.Date(from), as.Date(to), type)
    months <- format(dates, fmt)
    hbreaks<-unclass(as.POSIXct(dates))

    xx<-NULL;
    yy<-NULL;

    for ( i in seq(1,length(hbreaks)-1) )
    {
        # identify any tickets with a start time in range, lastreply in range
        # or where both start is less and lastreply is greater than the range
        t_sub <- t[which( (t$start < hbreaks[i] & t$lastreply > hbreaks[i+1]) | 
                          (t$start > hbreaks[i] & t$start <= hbreaks[i+1]) | 
                          (t$lastreply > hbreaks[i] & t$lastreply <= hbreaks[i+1]) ),]
        tickets <- length(t_sub$start)
        #if ( nrow(t_sub) > 0 ){
        #    for ( j in seq(1,nrow(t_sub)) )
        #    {
        #        #print(sprintf("id %s, date %s", t_sub[i,'ticket_id'], t_sub[i,'s1']))
        #        print(sprintf("id %s, date %s", t_sub[j,]$ticket_id, t_sub[j, 's1']))
        #    }
        #}

        xx<- c(xx, hbreaks[i])
        yy<- c(yy, tickets)

    }
    m<- months[1:length(months)-1]
    return (rbind(xx,yy,m))
}

online_nodes <- function (fb)
{
    breaks <- unique(fb$timestamp)
    n<-NULL
    o<-NULL
    x<-NULL
    for (i in seq(1,length(breaks)) )
    {
        ts <- breaks[i]
        sub <- fb[which(fb$timestamp == ts),]
        node_count   <- length(unique(sub$hostname))
        online_count <- length(unique(sub$hostname[which(sub$state=='BOOT')]))
        x<-c(x,ts)
        n<-c(n,node_count)
        o<-c(o,online_count)
    }
    print(length(x))
    print(length(n))
    print(length(o))
    return (rbind(x,n,o))
}

lowess_smooth <- function (x, y, delta=(60*60*24), f=0.02)
{
    a<-lowess(x, y, delta=delta, f=f)
    return (a);
}

#####

# system("parse_rt_data.py 3 > rt_data.csv");
t <- read.csv('rt_data_2004-2010.csv', sep=',', header=TRUE)
t2 <- t[which(t$complete == 1),]
ot <- open_tickets(t2, '2004/1/1', '2010/2/28', 'day', "%b")

start_image("rt_operator_overhead.png")
par(mfrow=c(2,1))
par(mai=c(0,1,0.1,0.1))

x1<-as.numeric(ot[1,])
y1<-as.numeric(ot[2,])

a_ot<-lowess_smooth(x1, y1)

plot(x1, y1, col='grey80', type='l', axes=F, 
    ylab="Open Tickets (tickets/day)", xlab="Date",
    ylim=c(0,120)) # , ylim=c(0,260))
lines(a_ot$x, round(a_ot$y), col='black')

#axis(1, labels=ot[3,], at=ot[1,], cex.axis=0.7)
axis(2, las=1)
#mtext("2004           2005           2006           2007           2008           2009", 1,2)

#abline_at_date('2005-01-01', 'grey60')
#abline_at_date('2006-01-01', 'grey60')
#abline_at_date('2007-01-01', 'grey60')
#abline_at_date('2008-01-01', 'grey60')
#abline_at_date('2009-01-01', 'grey60')
#abline_at_date('2010-01-01', 'grey60')
abline(h=25, lty=2, col='grey80')
abline(h=40, lty=2, col='grey80')

tstamp_20041112 <-abline_at_date("2004-11-12", col='grey60', lty=2)
tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=2)
tstamp_20050615 <-abline_at_date("2005-06-15", col='grey60', lty=2)
tstamp_20051023 <-abline_at_date("2005-10-23", col='grey60', lty=2)
tstamp_20070101 <-abline_at_date("2007-01-01", col='grey60', lty=2)
tstamp_20070501 <-abline_at_date("2007-05-01", col='grey60', lty=2)
tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=2)
tstamp_20080815 <-abline_at_date("2008-08-15", col='grey60', lty=2)
tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=2)
tstamp_20100201 <-abline_at_date("2010-02-01", col='white', lty=2)


text(x=c( tstamp_20041112+(tstamp_20050301-tstamp_20041112)/2,
        tstamp_20050301+(tstamp_20050615-tstamp_20050301)/2,
        tstamp_20050615+(tstamp_20051023-tstamp_20050615)/2,
        tstamp_20051023+(tstamp_20070101-tstamp_20051023)/2,
        tstamp_20070101+(tstamp_20070501-tstamp_20070101)/2,
        tstamp_20080601+(tstamp_20080815-tstamp_20080601)/2,
        tstamp_20090501+(tstamp_20100201-tstamp_20090501)/2 ),
     y=c(120),
     labels=c('3.0', '3.1', '3.1S', '3.2', '4.0', '4.2', '4.3')) 

par(mai=c(1,1,0.1,0.1))
for ( s in c(7) ) 
{
    d<- median_time_to_resolve_window(t2, "2004/1/1", "2010/2/28", s, "%b")
    plot(d[,1], exp(as.numeric(d[,5]))/24, type='l', lty=1, xlab="",
            axes=F, ylim=c(0.01, 15), ylab="Resolution Time by", col='grey50',
            xlim=c(min(x1), max(x1)))
    mtext("Quartile (days)", 2, 2)
    lines(d[,1], exp(as.numeric(d[,4]))/24, lty=1, col='black')
    lines(d[,1], exp(as.numeric(d[,3]))/24, lty=1, col='grey50')
    #axis(1, labels=d[,7], at=d[,1])
    axis(1, labels=ot[3,], at=ot[1,], cex.axis=0.7)
    mtext("2004           2005           2006           2007           2008           2009", 1,2)
    axis(2, las=1)
    m<-round(max(exp(as.numeric(d[,4]))/24), 2)
    axis(2, labels=m, at=m, las=1)
    abline(h=m, lty=2, col='grey40')
}

tstamp_20041112 <-abline_at_date("2004-11-12", col='grey60', lty=2)
tstamp_20050301 <-abline_at_date("2005-03-01", col='grey60', lty=2)
tstamp_20050615 <-abline_at_date("2005-06-15", col='grey60', lty=2)
tstamp_20051023 <-abline_at_date("2005-10-23", col='grey60', lty=2)
tstamp_20070101 <-abline_at_date("2007-01-01", col='grey60', lty=2)
tstamp_20070501 <-abline_at_date("2007-05-01", col='grey60', lty=2)
tstamp_20080601 <-abline_at_date("2008-06-01", col='grey60', lty=2)
tstamp_20080815 <-abline_at_date("2008-08-15", col='grey60', lty=2)
tstamp_20090501 <-abline_at_date("2009-05-01", col='grey60', lty=2)
tstamp_20100201 <-abline_at_date("2010-02-01", col='white', lty=2)


text(x=c( tstamp_20041112+(tstamp_20050301-tstamp_20041112)/2,
        tstamp_20050301+(tstamp_20050615-tstamp_20050301)/2,
        tstamp_20050615+(tstamp_20051023-tstamp_20050615)/2,
        tstamp_20051023+(tstamp_20070101-tstamp_20051023)/2,
        tstamp_20070101+(tstamp_20070501-tstamp_20070101)/2,
        tstamp_20080601+(tstamp_20080815-tstamp_20080601)/2,
        tstamp_20090501+(tstamp_20100201-tstamp_20090501)/2 ),
     y=c(15),
     labels=c('3.0', '3.1', '3.1S', '3.2', '4.0', '4.2', '4.3')) 

end_image()
