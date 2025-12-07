void rotprim(int primnum; float bias; string type){
    int pts[] = primpoints(0, primnum);
    int npts[];

    foreach(int i; int v; pts){
        vector pos1 = point(0, 'P', v);
        vector pos2 = point(0, 'P', pts[(i+1)%len(pts)]);
        vector pos = lerp(pos1, pos2, bias);
        int pt = addpoint(0, pos);
        append(npts, pt); 
    }

    int prim = addprim(0, type, npts);
    removeprim(0, primnum, 1);
    return;
}

