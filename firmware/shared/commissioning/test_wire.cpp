#include "wire.h"
#include "sd_wire.h"
#include <cassert>
#include <cstring>
using namespace flockwire;
int main() {
    uint8_t a[6]={1,2,3,4,5,6}, b[6]={6,5,4,3,2,1}, nonce[16]={9};
    Frame f{}; uint8_t body[4]={1,2,3,4};
    assert(encode(f,Kind::Poll,a,b,nonce,0x12345678,body,4));
    assert(f.size==76 && f.bytes[36]==0x78 && f.bytes[39]==0x12);
    View v{}; assert(decode(f.bytes,f.size,v));
    assert(v.kind==Kind::Poll && v.sequence==0x12345678 && v.length==4);
    assert(!decode(f.bytes,f.size-1,v));
    f.bytes[6]=161;assert(!decode(f.bytes,f.size,v));
    assert(!encode(f,Kind::Poll,a,b,nonce,0,body,161));
    assert(encode(f,Kind::Data,a,b,nonce,2,body,4));
    f.bytes[4]=2;assert(!decode(f.bytes,f.size,v));
    assert(label_index('A','1')==0 && label_index('D','4')==15 && label_index('E','1')==-1);
    TransferOrder order{}; order.begin(256);
    assert(order.accept(2,0,128)==Decision::Write);order.written(2,0,128);
    assert(order.accept(2,0,128)==Decision::Duplicate);
    assert(order.accept(3,129,127)==Decision::Reject);
    assert(order.accept(4,128,128)==Decision::Reject);
    assert(order.accept(3,128,129)==Decision::Reject);
    assert(order.accept(3,128,128)==Decision::Write);order.written(3,128,128);
    assert(order.complete() && order.next_sequence==4);
    uint8_t request[57]{};request[0]=2;
    assert(flocksd::request_valid(request,57));
    assert(!flocksd::request_valid(request,56));
    assert(!flocksd::request_valid(request,1));
    request[0]=1;assert(flocksd::request_valid(request,1));
    uint8_t report[flocksd::ReportSize]{};report[1]=1;
    assert(flocksd::report_valid(report,sizeof(report)));
    report[2]=9;assert(!flocksd::report_valid(report,sizeof(report)));report[2]=0;
    flocksd::put64(report+72,64021856256ULL);assert(flocksd::get64(report+72)==64021856256ULL);
    assert(encode(f,Kind::SdReply,a,b,nonce,3,report,sizeof(report)));
    assert(decode(f.bytes,f.size,v)&&v.kind==Kind::SdReply);
}
