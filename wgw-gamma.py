# wgw-gamma.idxl:  load gamma data

# 06/2018 wc converted to python3
# 05/09/2007 ges added more changes for the new file format.  This update is NO LONGER backwards compatible.
#            IMPORTANT:  THE '<' DETECTION COLUMN HAS BEEN MOVED FROM 10 TO 11.  THIS IS A MANUAL PROCESS
#                        THAT MUST BE PERFORMED ON THE RAW INPUT FILE.  THE VALUE OF COLUMN 9, the # COLUMN, IS NOW
#                        IGNORED.  THE VALUE OF COLUMN 10 IS IGNORED BY THE PARSE AS WELL.  THESE CHANGES
#                        WERE AGREED TO BY DAVID CLINE
# 05/03/2007 ges updated parse yet again.
# 10/19/2006 ges updated parse for current version of software.  This update should be backwards compatible.
#4/26/05 di original code

s3_process_id "WGW-GAMMA"
deptnum       "55"
dilution      1

find "ORTEC"
gosub stripm
#print(  aczdata &acz_data
calc version instr(acz_data,"G53W4.25")
if version > 0 then
   measureform "MM/DD/YY HH:MI:SS AM"
else
   measureform "DD-MON-YY HH24:MI:SS"
endif

on eof gamma_exit
on sqlerr parse_error
on formaterr parse_error

parse idx_datapath ////acz_instr/worknum
#parse idx_datapath /worknum
calc instrument_id upper(acz_instr)
calc worknum substr(worknum,1,6)
calc worknum "WG" || worknum

sql select prod into * from orderdetail where worknum = &worknum and
    deptnum = 55 and class != 'Q';
#CT031618 commenting out 2 sql statements below. It gets the groupid in parsetest, this query was causing it to get the wrong groupid if there was more than 1 prod for it.
#sql select groupid into * from prodgroup where prod = &prod
#    and groupid like 'RC-G-%';
#sql update workgroup qct_name = &groupid where worknum = &worknum;

find "Start time"
gosub stripm
calc acz_data onespace(acz_data)
calc acz_data translate(acz_data,"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ","0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ,")
parse acz_data ,,date,time
measuredate &date " " &time
rewind

find "Sample description"
skip
parse idx_data samplenum,dilution,

gosub getWGStat

if validwg = "FALSE" then
#    print(   "Invalid workgroup, no client samps?", worknum)
    exit
endif

gosub checksample
gosub s3_sampheader

if &qctype = "" then
#    print(  notqc
    parm_type "REG"
    usescn "FALSE"
else
    sql select pprodref into gammascn from ordermast where samplenum = &samplenum
        and prod = &prod;
    if found then
        usescn "TRUE"
    	sql select samp_joinid into gammascn_samp_joinid from sampheader
            where samplenum = &gammascn;
    else
        usescn "FALSE"
	    gammascn_samp_joinid ""
    endif
    parm_type  "FOUND"
#    print(  isqc
endif

if listmatclass = "SOLID" then
    units "pCi/g"
else
    units "pCi/L"
endif

# 10/19/2006 ges
# The new version of the software changed the report separator from +-+-+- to _______
# We first look for the new version.  If that is not found (that is, the file hits eof)
# we will then rewind the file and look for the old version.  If that fails, then time to exit
on eof gamma_exit
find "S U M M A R Y   O F   N U C L I D E S   I N   S A M P L E"
find "__________"
goto parseData

# The main parsing of the data section begins here
parseData:
on eof gamma_exit

while
#    print(  beginning of while loop
    uncertainty ""
    numvalue    ""
    error       ""
    file_rdl    ""
    file_mdl    ""
#  skip
    extract 11 lessthan 1
    extract 10 letterQual 1
    extract 9 pound 1
    extract 11 noinrange 5
    extract 3 blankline 4
    extract 3 endoffile 3

# ges 05/09/2007
# per DaveC we no longer care about the pound sign, so change it to something else
    if pound = "#" then
        pound "x"
    endif

    gosub stripm

    if endoffile = "---" then
        gosub gamma_exit
    endif
#Add a space between columns 8 and 9.  This is needed if the Nuclide is 7 characters in length.
    calc acz_data substr(acz_data, 1, 8) || " " || substr(acz_data, 9)
    calc acz_data onespace(acz_data)
    calc acz_data translate(acz_data,"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ","0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ,")

# We will either have 0, 1, or 2 fields between the parameter name and file_mdl value
# figure out how many there are so that the parse command works correctly.
    numberOfParseItems 0
    if pound != " " then
        if letterQual = " " then
		  if lessthan != " " then
		    numberOfParseItems 2
          else
		    numberOfParseItems 1
          endif
        else
	      numberOfParseItems 1
        endif
    else if letterQual != " " then
        numberOfParseItems 1
    else if lessthan != " " then
        numberOfParseItems 1
    endif

#print(  acz_data prior to if lessthan: ,acz_data

    if lessthan = "<" then
#	    print(  lessthan detected
	    if numberOfParseItems = 1 then
	        parse acz_data parmname,lessthan,file_mdl,num2,num3,num4,num5
        else
	        parse acz_data parmname,junk,lessthan,file_mdl,num2,num3,num4,num5
        endif
        sql select parm_stored,parm_syn into ps,parmname from parmdef where
	        parm_lookup = upper(&parmname);
	    if found then
#           Report the found value as well
            calc numvalue file_mdl
            if &num5 = "" then
	            calc file_rdl num3
	            calc file_mdl num4
	        else
	            if &num2 = ">12,HALFLIVES" then
	                calc file_mdl file_mdl
	            else
	                calc file_rdl num4
	                calc file_mdl num5
                endif
	        endif
	        if qc = "TRUE" then
	           parm_type "FOUND"
 	        else
	           parm_type "REG"
            endif
#            print(  About to call loadRCdata < true
#			print(  numvalue ,numvalue num2 ,num2
#		    print(  lessthan: numvalue ,numvalue file_mdl ,file_mdl file_rdl ,file_rdl
	        gosub loadRCdata
	        if usescn = "TRUE" then
	           gosub doscn
	        endif
#			print(  numvalue ,numvalue num2 ,num2
	        skip
	    else
	        skip
	    endif
    else
	    if pound = "#" then
	        if numberOfParseItems = 1 then
	            parse acz_data parmname,pound,numvalue,numvalue2,numvalue3,numvalue4,numvalue5
            else
	            parse acz_data parmname,pound,junk,numvalue,numvalue2,numvalue3,numvalue4,numvalue5
            endif
	        sql select parm_stored,parm_syn into ps,parmname from parmdef where
	            parm_lookup = upper(&parmname);
	        if found then
	            if &numvalue5 = "" then
#				print(  numvalue5 is empty
		            calc numvalue numvalue
		            calc uncertainty numvalue2
		            calc file_rdl numvalue3
		            calc file_mdl numvalue4
		        else
#				print(  numvalue5 is ,numvalue5
		            calc numvalue numvalue2
		            calc uncertainty numvalue4
		            calc file_rdl numvalue4
		            calc file_mdl numvalue5
		        endif
#				print(  file_mdl is ,file_mdl
		        if qc = "TRUE" then
		            parm_type "FOUND"
		        else
		            parm_type "REG"
		        endif
#                print(  About to call loadRCdata < false
		        gosub loadRCdata
		        if usescn = "TRUE" then
		            gosub doscn
		        endif
		        skip
	        else
	            skip
            endif
	    else
#		    print(  No lessthan in dataset
	        if noinrange = "No in" then
	            parse acz_data parmname,
	        else
	            parse acz_data parmname,
#				print(  lookup for parmname &parmname
		        sql select parm_stored,parm_syn into ps,parmname from parmdef where
		            parm_lookup = upper(&parmname);
                if numberOfParseItems = 0 then
                    parse acz_data parmname,numvalue,numvalue2,numvalue3,numvalue4,numvalue5
                else
                    parse acz_data parmname,junk,numvalue,numvalue2,numvalue3,numvalue4,numvalue5
                endif
		        sql select parm_stored,parm_syn into ps,parmname from parmdef where
		            parm_lookup = upper(&parmname);

# ges 05/03/2007 Add some checking to make sure we reach the end of the data
                calc nuclideSize length(parmname)

		        if found then
		           if nuclideSize > 2 then
		               if parmname = "#" then
                          print(  "**************************** GARY DOES NOT EXPECT TO SEE THIS"
		                   gosub gamma_exit
		               endif
		               if &numvalue5 = "" then
		                   calc numvalue numvalue
                           calc uncertainty numvalue2
			               calc file_rdl numvalue3
			               calc file_mdl numvalue4
	                   else
		                   calc numvalue numvalue2
			               calc uncertainty numvalue3
			               calc file_rdl numvalue4
			               calc file_mdl numvalue5
		               endif
		               if qc = "TRUE" then
                           parm_type "FOUND"
                       else
                           parm_type "REG"
                       endif
#print(  About to call loadRCdata no in false numvalue &numvalue file_mdl &file_mdl file_rdl &file_rdl
		               gosub loadRCdata
#print(  back from loadRCdata numvalue &numvalue file_mdl &file_mdl file_rdl &file_rdl
                       if usescn = "TRUE" then
			               gosub doscn
                       endif
                       skip
                    else
		               skip
                    endif
		        else
		            skip
		        endif
            endif
	    endif
    endif
end

doscn:
#    print(  in doscn samp_joinid &samp_joinid parm_type &parm_type
    sql update sampdata approval_status = '++' where
        samp_joinid = &samp_joinid and parm_type in ('FOUND','TRUE');
    sql select numvalue,units into numvalue,scnunits from sampdata where
        samp_joinid = &gammascn_samp_joinid and parm_stored = &ps
	    and parm_type = 'REG';
	if found then
	    parm_type "TRUE"
#        print(  &parmname in doscn
#ask sd1
	    gosub s3_sampdata
    endif
#   Repeated this SQL here to get the last item.  We could probably delete it from
#   a few lines above without harm.
    sql update sampdata approval_status = '++' where
        samp_joinid = &samp_joinid and parm_type in ('FOUND','TRUE');
return

loadRCdata:
#    print(  entering loadRCdata
    textvalue ""
    ifdef gammascn then
        if gammascn != "" then
            textvalue &gammascn
        endif
    endif
    sql select decode(&samp_type,'MSD','TRUE','DUP','TRUE','LCSSD','TRUE','FALSE')    into dodup from dual;
    if dodup = "TRUE" then
        gosub doraddup
    else
#        print(  about to call s3_sampdata &numvalue
        gosub s3_sampdata
#        print(  return from s2_sampdata &numvalue
    endif
return


doraddup:
    if numvalue != "" then
#        print(  doraddup &parmname &numvalue
#ask sd3
  	    gosub s3_sampdata
        numvalue ""
	    file_mdl ""
	    file_rdl ""
	    parm_type "RER"
	    gosub s3_sampdata
	    parm_type "FOUND"
    endif
return


gamma_exit:
#print(  gamma_exit numvalue &numvalue file_mdl &file_mdl
    sql update orderdetail dstatus = 'UPLD' where worknum = &worknum and
        samplenum = &samplenum and deptnum = 55;
#    print(  updating workgroup in gamma_exit ...
    print( Done.
exit

include parsetest.idxl
include s3data.idxl
