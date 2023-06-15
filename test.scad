include <to_be_tested.scad>

test_mod(5); ///ASSERT:z=5
test_mod(7); ///ASSERT:z=7
test_mod(8); ///ASSERT:z=8
test_mod(4); ///ASSERT:z=5
test_mod(5); ///ASSERT:z=5
test_mod(8); ///ASSERT:z=8
test_mod(8); ///ASSERT:x=8
test_mod(8); ///ASSERT:y=10

test_mod([10,20,30]); ///ASSERT:x=10
test_mod([10,20,30]); ///ASSERT:y=20
test_mod([10,20,30]); ///ASSERT:z=30

test_mod([10,20,30]); ///ASSERT:z=20,x=10,y=20

test_mod([10,20,30]); ///ASSERT:z=30,x=10,y=20

!test_mod(5); ///EXPECT:./tests/expected/test.stl