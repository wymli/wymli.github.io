package main

import "testing"

func TestGetCate(t *testing.T) {
	if cat, name := GetCateName("[asdf] a.md"); cat != "asdf" && name != "[asdf] a" {
		panic(cat + name)
	}
}
