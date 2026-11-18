#ifndef HGG_BDT_HEADERS_H
#define HGG_BDT_HEADERS_H

using namespace ROOT::VecOps;

template<typename container>
float Alt(container c, int index, float alt) {
    if (index < (int)c.size()) {
        return c[index];
    } else {
        return alt;
    }
}

RVec<double> LogVec(const RVec<double>& vec) {
    RVec<double> out;
    for (auto const& el : vec) {
        out.push_back(TMath::Log(el));
    }
    return out;
}

#endif