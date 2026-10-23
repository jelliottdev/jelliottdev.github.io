// Exhaustive source-defined first-L invertible singleton-crib scan over GF(29).
// Build: g++ -O3 -std=c++17 scan.cpp -o scan.exe
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
constexpr int Q=29, MAXL=5, MAXN=400;
struct Page {string id; vector<int> c,p;};
struct Tally {uint64_t invertible=0, full=0; int best=0; vector<string> samples;};
int invs[Q];
inline int mod(int v) {return v%Q;}
bool invert(const int a[MAXL][MAXL], int out[MAXL][MAXL], int L) {
    int m[MAXL][2*MAXL]{};
    for(int i=0;i<L;i++) {for(int j=0;j<L;j++) m[i][j]=a[i][j]; m[i][L+i]=1;}
    for(int col=0;col<L;col++) {
        int pivot=col; while(pivot<L && !m[pivot][col]) pivot++;
        if(pivot==L) return false;
        if(pivot!=col) for(int j=0;j<2*L;j++) swap(m[pivot][j],m[col][j]);
        int factor=invs[m[col][col]];
        for(int j=0;j<2*L;j++) m[col][j]=mod(m[col][j]*factor);
        for(int row=0;row<L;row++) if(row!=col) {
            factor=m[row][col];
            if(factor) for(int j=0;j<2*L;j++) m[row][j]=mod(m[row][j]+Q*Q*Q-factor*m[col][j]);
        }
    }
    for(int i=0;i<L;i++) for(int j=0;j<L;j++) out[i][j]=m[i][L+j];
    return true;
}
string sample(const int coeff[MAXL],const int state[MAXL],int L) {
    string s;
    for(int i=0;i<L;i++) {if(i) s+=','; s+=to_string(coeff[i]);}
    s+=':';
    for(int i=0;i<L;i++) {if(i) s+=','; s+=to_string(state[i]);}
    return s;
}
int main(int argc,char** argv) {
    if(argc<3 || argc>5) {cerr<<"usage: scan input.txt output.tsv [polynomial-limit-per-length] [optional-full-candidate-dump]\n";return 2;}
    for(int a=1;a<Q;a++) for(int b=1;b<Q;b++) if(a*b%Q==1) invs[a]=b;
    ifstream in(argv[1]); if(!in) return 3;
    int nPages; in>>nPages; vector<Page> pages(nPages);
    int maxPos=0;
    for(auto& p:pages) {
        int n,m; in>>p.id>>n>>m; p.c.resize(n);p.p.resize(m);
        for(int& v:p.c) in>>v;
        for(int& v:p.p) {in>>v;maxPos=max(maxPos,v);}
        if(!in || m<5 || n>=MAXN || p.p.back()>=n) return 4;
    }
    uint64_t limit=argc==4?stoull(argv[3]):UINT64_MAX;
    if(argc==5) limit=stoull(argv[3]);
    ofstream dump;
    if(argc==5) {dump.open(argv[4]);if(!dump) return 6;dump<<"page\tlength\tmode\tcoefficients:state\n";}
    vector<array<array<Tally,2>,6>> tally(nPages); // mode 0=sub, 1=beaufort; add is a signed duplicate of sub
    int alpha[MAXN][MAXL]{}, coeff[MAXL]{};
    for(int L=1;L<=5;L++) {
        uint64_t total=1;for(int j=0;j<L;j++) total*=Q;
        uint64_t stop=min(total,limit);
        cerr<<"L="<<L<<" polynomials="<<stop<<"/"<<total<<"\n";
        for(uint64_t code=0;code<stop;code++) {
            uint64_t tmp=code;
            for(int j=0;j<L;j++) {coeff[j]=tmp%Q;tmp/=Q;}
            for(int i=0;i<L;i++) for(int j=0;j<L;j++) alpha[i][j]=i==j;
            for(int i=L;i<=maxPos;i++) for(int j=0;j<L;j++) {
                int sum=0;for(int k=0;k<L;k++) sum+=coeff[k]*alpha[i-L+k][j];
                alpha[i][j]=mod(sum);
            }
            for(int pi=0;pi<nPages;pi++) {
                auto& pg=pages[pi];
                int a[MAXL][MAXL]{}, inverse[MAXL][MAXL]{};
                for(int i=0;i<L;i++) for(int j=0;j<L;j++) a[i][j]=alpha[pg.p[i]][j];
                if(!invert(a,inverse,L)) continue;
                for(int mode=0;mode<2;mode++) tally[pi][L][mode].invertible++;
                for(int mask=0;mask<(1<<L);mask++) for(int mode=0;mode<2;mode++) {
                    int rhs[MAXL]{},state[MAXL]{};
                    for(int i=0;i<L;i++) {
                        int plain=mask&(1<<i)?24:10;
                        rhs[i]=mode==0?mod(pg.c[pg.p[i]]+Q-plain):mod(pg.c[pg.p[i]]+plain);
                    }
                    for(int j=0;j<L;j++) {int sum=0;for(int i=0;i<L;i++) sum+=inverse[j][i]*rhs[i];state[j]=mod(sum);}
                    int matches=L;
                    for(size_t i=L;i<pg.p.size();i++) {
                        int key=0;for(int j=0;j<L;j++) key+=alpha[pg.p[i]][j]*state[j];key=mod(key);
                        int plain=mode==0?mod(pg.c[pg.p[i]]+Q-key):mod(key+Q-pg.c[pg.p[i]]);
                        if(plain==10 || plain==24) matches++;
                    }
                    auto& t=tally[pi][L][mode];
                    t.best=max(t.best,matches);
                    if(matches==(int)pg.p.size()) {
                        t.full++;
                        string s=sample(coeff,state,L);
                        if(t.samples.size()<5) t.samples.push_back(s);
                        if(dump) dump<<pg.id<<'\t'<<L<<'\t'<<(mode==0?"sub":"beaufort")<<'\t'<<s<<'\n';
                    }
                }
            }
        }
    }
    ofstream out(argv[2]);if(!out) return 5;
    out<<"page\tlength\tmode\tpolynomials\tinvertible\tbest\tfull\tsamples\n";
    for(int pi=0;pi<nPages;pi++) for(int L=1;L<=5;L++) for(int mode=0;mode<3;mode++) {
        auto t=tally[pi][L][mode==2?1:0];
        uint64_t total=1;for(int j=0;j<L;j++) total*=Q;
        out<<pages[pi].id<<'\t'<<L<<'\t'<<(mode==0?"sub":mode==1?"add":"beaufort")
           <<'\t'<<min(total,limit)<<'\t'<<t.invertible<<'\t'<<t.best<<'\t'<<t.full<<'\t';
        for(size_t i=0;i<t.samples.size();i++) {
            if(i) out<<';';
            if(mode==1) {
                auto s=t.samples[i];auto pos=s.find(':');out<<s.substr(0,pos)<<':';
                string x=s.substr(pos+1);size_t at=0;bool first=true;
                while(at<x.size()) {size_t end=x.find(',',at);if(end==string::npos) end=x.size();if(!first) out<<',';out<<(Q-stoi(x.substr(at,end-at)))%Q;first=false;at=end+1;}
            } else out<<t.samples[i];
        }
        out<<'\n';
    }
}
