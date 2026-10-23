#include "core.h"
#include "pages.h"
#include "secrets.h"
#include "Transformers.h"
#include <iostream>
#include <set>
#include <vector>
using namespace core;
int count_launches(std::string_view raw) {
  ProcessedText pt(raw); auto words=pt.get_words();
  std::set<int> mp(secrets::MISSING_PRIMES_2013.begin(),secrets::MISSING_PRIMES_2013.end());
  int run=0,launches=0;
  for (auto& word:words) {
    int sum=pt.calculate_gp_sum(word);
    bool hit=(mp.count(sum)&&(word.size()>1||sum>120))||mp.count(3301-sum);
    run=hit?run+1:0;
    if(run>=3) ++launches;
  }
  return launches;
}
int main(){
 init_tables();
 std::cout << "three_anchor " << count_launches("ᚠᛗ-ᚢᚦᛗ-ᚩᚦᛗ") << "\n";
 std::cout << "broken_anchor " << count_launches("ᚠᛗ-ᚢᚦᛗ-ᚠ-ᚩᚦᛗ") << "\n";
 auto& page=G_PAGES[4];
 ProcessedText plain(page.content,page.index);
 auto original=plain.indices();
 for(auto keywhich:{0,1}) {
  std::vector<int> key;
  if(keywhich==0){ for(auto str:secrets::CUNEIFORM_STREAM){int n=0;for(char c:str){int d=c>='0'&&c<='9'?c-'0':c>='A'&&c<='Z'?c-'A'+10:c-'a'+36;n=n*60+d;}key.push_back(n%29);} }
  else {for(int p:secrets::MISSING_PRIMES_2013)key.push_back(p%29);}
  auto& x=plain.indices();x=original;int i=0;
  for(auto& c:x)if(c<29){int p=c;c=static_cast<uint8_t>((28+3-p+key[i%key.size()])%29);++i;}
  int j=0;for(auto& c:x)if(c<29){c=static_cast<uint8_t>((c-key[j%key.size()]+29)%29);++j;}
  AtbashTransformer(3).transform(plain);
  std::cout << "key_"<<keywhich<<"_recovered " <<(plain.indices()==original)<<" runes "<<i<<" key_len "<<key.size()<<"\n";
 }
}
